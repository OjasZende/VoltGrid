import pyomo.environ as pyo
from extraction_script import extract_spatial_data
from distance_matrix import calculate_distance_matrix

GLPK_PATH = r"C:\Users\Ankit\Desktop\HackX 2.0\winglpk-4.65\glpk-4.65\w64\glpsol.exe"

# Default station budget — can be overridden via solve_mclp(K=...)
DEFAULT_K = 10


def solve_mclp(candidate_sites, demand_points, demand_weights, reachability_map, K=DEFAULT_K):
    """
    Maximal Covering Location Problem (MCLP) using Pyomo + GLPK.

    Given a fixed budget of K stations, choose which candidate sites to
    activate so that the **total weighted demand covered** is maximised.
    A demand point i is "covered" if at least one selected station is
    within 2000 m driving distance.

    Formulation
    -----------
    Variables:
        x[j] ∈ {0,1}  — 1 if station placed at candidate j
        y[i] ∈ {0,1}  — 1 if demand point i is covered

    Objective:
        maximize  Σ_i  w[i] * y[i]

    Subject to:
        Σ_j  x[j]            ≤ K                    (budget)
        y[i] ≤ Σ_{j∈N(i)} x[j]   for all i          (coverage linkage)
        x[j], y[i] ∈ {0,1}

    Parameters
    ----------
    candidate_sites  : list of (lat, lon)
    demand_points    : list of (lat, lon)
    demand_weights   : dict  {demand_index: weight}
    reachability_map : dict  {demand_index: [candidate_indices]}
    K                : int   — station budget

    Returns
    -------
    selected_coords : list of (lat, lon)  — coordinates of selected stations
    """
    num_candidates = len(candidate_sites)
    num_demand     = len(demand_points)

    # Separate coverable / uncoverable demand points
    uncoverable = [i for i in range(num_demand) if not reachability_map.get(i, [])]
    coverable   = [i for i in range(num_demand) if reachability_map.get(i, [])]

    if uncoverable:
        print(f"  INFO: {len(uncoverable)} demand points have no reachable candidate — excluded from model.")
    print(f"  Coverable demand points: {len(coverable)} / {num_demand}")

    total_weight = sum(demand_weights.get(i, 0) for i in coverable)
    print(f"  Total coverable weight: {total_weight}  (K={K} stations)")

    # ── Build Pyomo model ────────────────────────────────────────────────────
    model = pyo.ConcreteModel("MCLP_EV_Stations")

    model.J = pyo.Set(initialize=range(num_candidates), doc="Candidate site indices")
    model.I = pyo.Set(initialize=coverable,             doc="Coverable demand point indices")

    # x[j]: binary — place station at candidate j
    model.x = pyo.Var(model.J, domain=pyo.Binary, doc="1 if station placed at candidate j")

    # y[i]: binary — demand point i is covered
    model.y = pyo.Var(model.I, domain=pyo.Binary, doc="1 if demand point i is covered")

    # Objective: maximise total weighted demand covered
    model.obj = pyo.Objective(
        expr=sum(demand_weights.get(i, 0) * model.y[i] for i in model.I),
        sense=pyo.maximize,
        doc="Maximise total weighted demand covered"
    )

    # Budget constraint: at most K stations
    model.budget = pyo.Constraint(
        expr=sum(model.x[j] for j in model.J) <= K,
        doc="Station budget"
    )

    # Coverage linkage: y[i] = 1 only if at least one covering station is open
    # y[i] <= Σ_{j in N(i)} x[j]
    # Since we maximise y, the solver will push y[i] to 1 whenever possible.
    def coverage_rule(model, i):
        neighbours = reachability_map[i]
        return model.y[i] <= sum(model.x[j] for j in neighbours)

    model.coverage = pyo.Constraint(model.I, rule=coverage_rule,
                                     doc="Demand point covered only if a station reaches it")

    # ── Solve ────────────────────────────────────────────────────────────────
    print(f"\nSolving MCLP with GLPK  (budget K={K})...")
    solver = pyo.SolverFactory("glpk", executable=GLPK_PATH)
    result = solver.solve(model, tee=False)

    if (result.solver.status == pyo.SolverStatus.ok and
            result.solver.termination_condition == pyo.TerminationCondition.optimal):
        print("  [OK] Optimal solution found.")
    else:
        print(f"  Solver status            : {result.solver.status}")
        print(f"  Termination condition    : {result.solver.termination_condition}")
        return []

    # ── Extract results ──────────────────────────────────────────────────────
    selected_indices  = [j for j in model.J if pyo.value(model.x[j]) > 0.5]
    selected_coords   = [candidate_sites[j] for j in selected_indices]
    covered_indices   = [i for i in model.I if pyo.value(model.y[i]) > 0.5]
    achieved_weight   = sum(demand_weights.get(i, 0) for i in covered_indices)

    print(f"\n  Stations placed       : {len(selected_indices)} / {K} budget used")
    print(f"  Demand points covered : {len(covered_indices)} / {len(coverable)}")
    print(f"  Weight covered        : {achieved_weight} / {total_weight}"
          f"  ({100*achieved_weight/total_weight:.1f}%)" if total_weight else "")

    print(f"\nSelected Station Coordinates (Lat, Lon):")
    for idx, coord in zip(selected_indices, selected_coords):
        print(f"  Site {idx:>3}: ({coord[0]:.7f}, {coord[1]:.7f})")

    return selected_coords


if __name__ == "__main__":
    graph_file = "data/mumbai_network.graphml"

    # Step 1: Extract candidate sites, demand points, and POI-based weights
    candidate_sites, demand_points, demand_weights = extract_spatial_data(graph_file)

    # Step 2: Calculate the reachability / distance matrix
    reachability = calculate_distance_matrix(graph_file, demand_points, candidate_sites)

    # Step 3: Solve MCLP with a budget of K stations
    K = 10   # ← adjust budget here
    selected = solve_mclp(candidate_sites, demand_points, demand_weights, reachability, K=K)
