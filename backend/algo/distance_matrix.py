import re
import osmnx as ox
import networkx as nx
from extraction_script import extract_spatial_data

# ---------------------------------------------------------------------------
# Speed / time constants
# ---------------------------------------------------------------------------

# 0.5x multiplier applied to every speed → simulates peak-hour congestion
PEAK_HOUR_MULTIPLIER = 0.5

# Fallback free-flow speeds (km/h) by OSM highway tag when maxspeed is absent
HIGHWAY_SPEED_DEFAULTS = {
    "motorway":       100,
    "trunk":           80,
    "primary":         60,
    "secondary":       50,
    "tertiary":        40,
    "unclassified":    30,
    "residential":     25,
    "living_street":   10,
    "service":         15,
    "motorway_link":   60,
    "trunk_link":      50,
    "primary_link":    40,
    "secondary_link":  30,
    "tertiary_link":   25,
    "road":            30,    # generic fallback
}
DEFAULT_SPEED_KMH = 30        # last-resort fallback when tag is unrecognised

# Reachability cutoff: seconds of peak-hour travel time
# 600 s = 10 minutes at congested speed (≈ 2 km free-flow @ 30 km/h with 0.5x)
TRAVEL_TIME_CUTOFF_SECONDS = 600


def _parse_maxspeed(value) -> float | None:
    """
    Parse an OSM `maxspeed` tag value to km/h.

    Handles:
      - Numeric strings:  "50", "50.0"
      - mph values:       "30 mph"
      - Special tags:     "walk" → 5, "none" / "unlimited" → None (use default)
      - Lists:            takes the minimum (most conservative)

    Returns None if speed cannot be determined.
    """
    if value is None:
        return None

    # Some edges store multiple values as a list — take the minimum
    if isinstance(value, list):
        parsed = [_parse_maxspeed(v) for v in value]
        valid  = [s for s in parsed if s is not None]
        return min(valid) if valid else None

    val = str(value).strip().lower()

    if val in ("none", "unlimited", "signals", "variable"):
        return None   # uncontrolled — fall back to highway default
    if val == "walk":
        return 5.0

    # mph conversion
    mph_match = re.match(r"([\d.]+)\s*mph", val)
    if mph_match:
        return float(mph_match.group(1)) * 1.60934

    # plain numeric
    num_match = re.match(r"^([\d.]+)", val)
    if num_match:
        return float(num_match.group(1))

    return None


def _add_travel_time_weights(G, peak_multiplier: float = PEAK_HOUR_MULTIPLIER):
    """
    Annotate every directed edge in G with a `travel_time` attribute (seconds).

    travel_time = (length_m / 1000) / effective_speed_kmh  × 3600
    effective_speed_kmh = raw_speed × peak_multiplier

    Modifies the graph in-place and returns it.
    """
    for u, v, data in G.edges(data=True):
        length_m  = data.get("length", 0)               # metres

        # 1. Try OSM maxspeed tag
        raw_speed = _parse_maxspeed(data.get("maxspeed"))

        # 2. Fall back to highway-type default
        if raw_speed is None:
            highway   = data.get("highway", "road")
            if isinstance(highway, list):
                highway = highway[0]
            raw_speed = HIGHWAY_SPEED_DEFAULTS.get(highway, DEFAULT_SPEED_KMH)

        # 3. Apply peak-hour multiplier  →  congested speed
        effective_speed_kmh = max(raw_speed * peak_multiplier, 1.0)  # floor at 1 km/h

        # 4. seconds = (km) / (km/h) × 3600
        travel_time_s = (length_m / 1000.0) / effective_speed_kmh * 3600.0
        data["travel_time"] = travel_time_s

    return G


def calculate_distance_matrix(
    graph_path,
    demand_points,
    candidate_sites,
    peak_multiplier: float = PEAK_HOUR_MULTIPLIER,
    cutoff_seconds: float  = TRAVEL_TIME_CUTOFF_SECONDS,
):
    """
    Build a reachability map using travel-time Dijkstra.

    For every demand point, find all candidate sites reachable within
    `cutoff_seconds` of peak-hour driving time (OSM maxspeed × 0.5).

    Parameters
    ----------
    graph_path      : str   — path to the .graphml road network file
    demand_points   : list of (lat, lon)
    candidate_sites : list of (lat, lon)
    peak_multiplier : float — speed reduction factor (default 0.5 = peak hour)
    cutoff_seconds  : float — max travel time in seconds (default 600 = 10 min)

    Returns
    -------
    reachability_map : dict {demand_index: [candidate_indices]}
    """
    print(f"Loading graph from {graph_path}...")
    G = ox.load_graphml(graph_path)

    print(f"Computing peak-hour travel times  "
          f"(speed multiplier={peak_multiplier}, cutoff={cutoff_seconds}s)...")
    G = _add_travel_time_weights(G, peak_multiplier=peak_multiplier)

    # ── Map coordinates to nearest graph nodes ────────────────────────────────
    print("Mapping coordinates to nearest nodes...")
    demand_lats    = [p[0] for p in demand_points]
    demand_lons    = [p[1] for p in demand_points]
    demand_nodes   = ox.nearest_nodes(G, X=demand_lons, Y=demand_lats)

    candidate_lats  = [s[0] for s in candidate_sites]
    candidate_lons  = [s[1] for s in candidate_sites]
    candidate_nodes = ox.nearest_nodes(G, X=candidate_lons, Y=candidate_lats)

    # node_id → list of candidate indices (multiple sites can share one node)
    node_to_cand_indices = {}
    for idx, node in enumerate(candidate_nodes):
        node_to_cand_indices.setdefault(node, []).append(idx)

    # node_id → list of demand indices
    node_to_demand_indices = {}
    for idx, node in enumerate(demand_nodes):
        node_to_demand_indices.setdefault(node, []).append(idx)

    unique_demand_nodes = list(node_to_demand_indices.keys())
    reachability_map    = {}

    print(f"Running Dijkstra on {len(unique_demand_nodes)} unique demand nodes "
          f"(weight=travel_time, cutoff={cutoff_seconds}s)...")

    for i, d_node in enumerate(unique_demand_nodes):
        if i % 50 == 0:
            print(f"  Processing demand node group {i}/{len(unique_demand_nodes)}...")

        try:
            # Returns {node_id: travel_time_seconds} within cutoff
            times = nx.single_source_dijkstra_path_length(
                G, d_node, cutoff=cutoff_seconds, weight="travel_time"
            )

            # Collect candidate indices for all reachable candidate nodes
            reachable_cands = sorted({
                c_idx
                for node in times
                if node in node_to_cand_indices
                for c_idx in node_to_cand_indices[node]
            })

            for d_idx in node_to_demand_indices[d_node]:
                reachability_map[d_idx] = reachable_cands

        except nx.NetworkXNoPath:
            for d_idx in node_to_demand_indices[d_node]:
                reachability_map[d_idx] = []

    covered = sum(1 for v in reachability_map.values() if v)
    print(f"\nReachability complete: {covered} / {len(demand_points)} demand "
          f"points have at least one candidate within {cutoff_seconds}s peak-hour travel.")

    return reachability_map


if __name__ == "__main__":
    graph_file = "data/mumbai_network.graphml"

    # Extract data first (now returns 3 values)
    candidate_sites, demand_points, demand_weights = extract_spatial_data(graph_file)

    # Calculate reachability using travel-time Dijkstra
    reachability = calculate_distance_matrix(
        graph_file, demand_points, candidate_sites
    )

    print(f"\nCompleted reachability map for {len(reachability)} demand points.")

    sample_idx = 0
    if sample_idx in reachability:
        print(f"Demand point {sample_idx} is reachable from "
              f"{len(reachability[sample_idx])} candidate sites within "
              f"{TRAVEL_TIME_CUTOFF_SECONDS}s peak-hour travel.")
        print(f"Reachable candidate indices: {reachability[sample_idx]}")
