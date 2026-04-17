import os
import math
import pyomo.environ as pyo
from extraction_script import extract_spatial_data
from distance_matrix import calculate_distance_matrix

# Dynamically resolve GLPK path relative to this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GLPK_PATH = os.path.join(BASE_DIR, "winglpk-4.65", "glpk-4.65", "w64", "glpsol.exe")

# Default station budget
DEFAULT_K = 10

# Grid congestion: at most this many stations within 1km of any one substation
MAX_STATIONS_PER_SUBSTATION = 1
SUBSTATION_RADIUS_KM        = 1.0


# ---------------------------------------------------------------------------
# Spatial helpers
# ---------------------------------------------------------------------------

def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance in km between two (lat, lon) points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlam  = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_substation_neighborhoods(candidate_sites, substations,
                                    radius_km=SUBSTATION_RADIUS_KM):
    """
    For each substation, return the indices of candidate sites within
    `radius_km` straight-line distance.

    Returns
    -------
    neighborhoods : list of lists
        neighborhoods[s] = [j, j, ...] candidate indices near substation s
        Only substations with >= 1 nearby candidate are included.
    """
    neighborhoods = []
    for s_lat, s_lon in substations:
        nearby = [
            j for j, (c_lat, c_lon) in enumerate(candidate_sites)
            if _haversine_km(s_lat, s_lon, c_lat, c_lon) <= radius_km
        ]
        if nearby:                          # only add if at least one candidate nearby
            neighborhoods.append(nearby)
    return neighborhoods


# ---------------------------------------------------------------------------
# MCLP solver
# ---------------------------------------------------------------------------

def solve_mclp(candidate_sites, demand_points, demand_weights,
               reachability_map, K=DEFAULT_K, substations=None):
    """
    Maximal Covering Location Problem (MCLP) using Pyomo + GLPK.

    Given a fixed budget of K stations, choose which candidate sites to
    activate so that the total weighted demand covered is maximised,
    subject to a grid-congestion constraint near electrical substations.

    Formulation
    -----------
    Variables:
        x[j] in {0,1}  -- 1 if station placed at candidate j
        y[i] in {0,1}  -- 1 if demand point i is covered

    Objective:
        maximize  sum_i  w[i] * y[i]

    Subject to:
        sum_j  x[j]                    <= K          (budget)
        y[i]  <= sum_{j in N(i)} x[j]  for all i    (coverage linkage)
        sum_{j in S(s)} x[j]           <= MAX_PER_SUBSTATION
                                        for all s    (grid congestion)
        x[j], y[i] in {0,1}

    Parameters
    ----------
    candidate_sites  : list of (lat, lon)
    demand_points    : list of (lat, lon)
    demand_weights   : dict  {demand_index: weight}
    reachability_map : dict  {demand_index: [candidate_indices]}
    K                : int   -- station budget
    substations      : list of (lat, lon) | None
                       OSM electrical substations; if None the grid-congestion
                       constraint is skipped.

    Returns
    -------
    selected_coords : list of (lat, lon)
    """
    num_candidates = len(candidate_sites)
    num_demand     = len(demand_points)

    uncoverable = [i for i in range(num_demand) if not reachability_map.get(i, [])]
    coverable   = [i for i in range(num_demand) if reachability_map.get(i, [])]

    if uncoverable:
        print(f"  INFO: {len(uncoverable)} demand points have no reachable candidate -- excluded.")
    print(f"  Coverable demand points : {len(coverable)} / {num_demand}")

    total_weight = sum(demand_weights.get(i, 0) for i in coverable)
    print(f"  Total coverable weight  : {total_weight}  (K={K} stations)")

    # -- Substation neighborhoods -------------------------------------------
    sub_neighborhoods = []
    if substations:
        sub_neighborhoods = _build_substation_neighborhoods(
            candidate_sites, substations, radius_km=SUBSTATION_RADIUS_KM
        )
        total_constrained = sum(len(n) for n in sub_neighborhoods)
        print(f"  Grid-congestion groups  : {len(sub_neighborhoods)} substations "
              f"touching {total_constrained} candidate slots "
              f"(max {MAX_STATIONS_PER_SUBSTATION} per substation, "
              f"radius={SUBSTATION_RADIUS_KM} km)")
    else:
        print("  Grid-congestion constraint: SKIPPED (no substations provided)")

    # -- Build Pyomo model ---------------------------------------------------
    model = pyo.ConcreteModel("MCLP_EV_Stations")

    model.J = pyo.Set(initialize=range(num_candidates), doc="Candidate site indices")
    model.I = pyo.Set(initialize=coverable,             doc="Coverable demand point indices")

    model.x = pyo.Var(model.J, domain=pyo.Binary, doc="1 if station at candidate j")
    model.y = pyo.Var(model.I, domain=pyo.Binary, doc="1 if demand point i is covered")

    # Objective
    model.obj = pyo.Objective(
        expr=sum(demand_weights.get(i, 0) * model.y[i] for i in model.I),
        sense=pyo.maximize,
        doc="Maximise total weighted demand covered"
    )

    # Budget constraint
    model.budget = pyo.Constraint(
        expr=sum(model.x[j] for j in model.J) <= K,
        doc="Station budget"
    )

    # Coverage linkage
    def coverage_rule(model, i):
        return model.y[i] <= sum(model.x[j] for j in reachability_map[i])

    model.coverage = pyo.Constraint(model.I, rule=coverage_rule,
                                     doc="Demand point covered only if a station reaches it")

    # Grid-congestion constraint
    # For each substation s, at most MAX_STATIONS_PER_SUBSTATION candidates
    # within SUBSTATION_RADIUS_KM may be selected simultaneously.
    if sub_neighborhoods:
        model.S = pyo.Set(initialize=range(len(sub_neighborhoods)),
                          doc="Substation neighborhood indices")

        def grid_congestion_rule(model, s):
            return sum(model.x[j] for j in sub_neighborhoods[s]) \
                   <= MAX_STATIONS_PER_SUBSTATION

        model.grid_congestion = pyo.Constraint(
            model.S, rule=grid_congestion_rule,
            doc=f"Max {MAX_STATIONS_PER_SUBSTATION} station(s) within "
                f"{SUBSTATION_RADIUS_KM} km of any substation"
        )

    # -- Solve ---------------------------------------------------------------
    print(f"\nSolving MCLP with GLPK  (budget K={K})...")
    solver = pyo.SolverFactory("glpk", executable=GLPK_PATH)
    result = solver.solve(model, tee=False)

    if (result.solver.status == pyo.SolverStatus.ok and
            result.solver.termination_condition == pyo.TerminationCondition.optimal):
        print("  [OK] Optimal solution found.")
    else:
        print(f"  Solver status         : {result.solver.status}")
        print(f"  Termination condition : {result.solver.termination_condition}")
        return []

    # -- Extract results -----------------------------------------------------
    selected_indices = [j for j in model.J if pyo.value(model.x[j]) > 0.5]
    selected_coords  = [candidate_sites[j] for j in selected_indices]
    covered_indices  = [i for i in model.I if pyo.value(model.y[i]) > 0.5]
    achieved_weight  = sum(demand_weights.get(i, 0) for i in covered_indices)

    print(f"\n  Stations placed       : {len(selected_indices)} / {K} budget used")
    print(f"  Demand points covered : {len(covered_indices)} / {len(coverable)}")
    if total_weight:
        print(f"  Weight covered        : {achieved_weight} / {total_weight}"
              f"  ({100 * achieved_weight / total_weight:.1f}%)")

    print(f"\nSelected Station Coordinates (Lat, Lon):")
    for idx, coord in zip(selected_indices, selected_coords):
        print(f"  Site {idx:>3}: ({coord[0]:.7f}, {coord[1]:.7f})")

    return selected_coords


if __name__ == "__main__":
    graph_file = "data/mumbai_network.graphml"

    # Step 1: Extract candidate sites, demand points, POI weights, substations
    candidate_sites, demand_points, demand_weights, substations = \
        extract_spatial_data(graph_file)

    # Step 2: Calculate travel-time reachability matrix
    reachability = calculate_distance_matrix(graph_file, demand_points, candidate_sites)

    # Step 3: Solve MCLP with grid-congestion constraint
    K = 10   # <- adjust budget here
    selected = solve_mclp(
        candidate_sites, demand_points, demand_weights,
        reachability, K=K, substations=substations
    )
