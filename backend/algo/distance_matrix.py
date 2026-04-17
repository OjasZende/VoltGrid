import osmnx as ox
import networkx as nx
from extraction_script import extract_spatial_data

def calculate_distance_matrix(graph_path, demand_points, candidate_sites):
    print(f"Loading graph from {graph_path}...")
    G = ox.load_graphml(graph_path)
    
    # Map coordinates to nearest nodes
    print("Mapping coordinates to nearest nodes...")
    demand_lats = [p[0] for p in demand_points]
    demand_lons = [p[1] for p in demand_points]
    demand_nodes = ox.nearest_nodes(G, X=demand_lons, Y=demand_lats)
    
    candidate_lats = [s[0] for s in candidate_sites]
    candidate_lons = [s[1] for s in candidate_sites]
    candidate_nodes = ox.nearest_nodes(G, X=candidate_lons, Y=candidate_lats)
    
    # Store candidates by their node ID for quick lookup
    # A single node might represent multiple candidate sites
    node_to_cand_indices = {}
    for idx, node in enumerate(candidate_nodes):
        if node not in node_to_cand_indices:
            node_to_cand_indices[node] = []
        node_to_cand_indices[node].append(idx)
        
    reachability_map = {}
    
    print("Calculating driving distances with 2000m cutoff...")
    # Iterate through unique demand nodes to save computations
    # Map each demand_node to its original indices in demand_points
    node_to_demand_indices = {}
    for idx, node in enumerate(demand_nodes):
        if node not in node_to_demand_indices:
            node_to_demand_indices[node] = []
        node_to_demand_indices[node].append(idx)
        
    unique_demand_nodes = list(node_to_demand_indices.keys())
    
    for i, d_node in enumerate(unique_demand_nodes):
        if i % 50 == 0:
            print(f"Processing demand node group {i}/{len(unique_demand_nodes)}...")
            
        # Find all nodes within 2000m driving distance
        # single_source_dijkstra_path_length returns {node_id: distance}
        try:
            lengths = nx.single_source_dijkstra_path_length(G, d_node, cutoff=2000, weight='length')
            
            # Identify which of these nodes are candidate sites
            reachable_cands = []
            for node in lengths:
                if node in node_to_cand_indices:
                    reachable_cands.extend(node_to_cand_indices[node])
            
            # Sort and unique to be clean
            reachable_cands = sorted(list(set(reachable_cands)))
            
            # Update the map for all demand points that share this node
            for d_idx in node_to_demand_indices[d_node]:
                reachability_map[d_idx] = reachable_cands
        except nx.NetworkXNoPath:
            for d_idx in node_to_demand_indices[d_node]:
                reachability_map[d_idx] = []
                
    return reachability_map

if __name__ == "__main__":
    graph_file = "data/mumbai_network.graphml"
    
    # Extract data first
    candidate_sites, demand_points = extract_spatial_data(graph_file)
    
    # Calculate reachability
    reachability = calculate_distance_matrix(graph_file, demand_points, candidate_sites)
    
    print(f"\nCompleted reachability map for {len(reachability)} demand points.")
    
    # Verification check
    sample_idx = 0
    if sample_idx in reachability:
        print(f"Sample Demand Point {sample_idx} is within 2000m of {len(reachability[sample_idx])} candidate sites.")
        print(f"Reachable candidate indices: {reachability[sample_idx]}")
