import osmnx as ox
import sys

graph_path = "data/mumbai_network.graphml"
print(f"Loading {graph_path}...")
try:
    G = ox.load_graphml(graph_path)
    print("Graph loaded.")
    gdf_nodes, _ = ox.graph_to_gdfs(G)
    bounds = gdf_nodes.total_bounds
    print(f"Bounds (W, S, E, N): {bounds}")
    print(f"CRS: {gdf_nodes.crs}")
except Exception as e:
    print(f"Error: {e}")
sys.stdout.flush()
