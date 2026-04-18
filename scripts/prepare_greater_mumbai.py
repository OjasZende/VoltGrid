import osmnx as ox
import os
import sys

# Add backend/algo to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend", "algo"))
from spatial_config import BOUNDS, GREATER_MUMBAI_GRAPH

def main():
    print(f"Preparing Greater Mumbai Graph...")
    print(f"Bounds: {BOUNDS}")
    
    west, south, east, north = BOUNDS
    
    if os.path.exists(GREATER_MUMBAI_GRAPH):
        print(f"Graph already exists at {GREATER_MUMBAI_GRAPH}")
        return

    print("Downloading graph from OSM (this may take a few minutes)...")
    # Download drivable network for the bbox
    # bbox order for ox 2.x is (west, south, east, north)
    G = ox.graph_from_bbox(bbox=BOUNDS, network_type='drive')
    
    print(f"Graph downloaded. Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")
    
    os.makedirs(os.path.dirname(GREATER_MUMBAI_GRAPH), exist_ok=True)
    ox.save_graphml(G, GREATER_MUMBAI_GRAPH)
    print(f"Saved Greater Mumbai graph to {GREATER_MUMBAI_GRAPH}")

if __name__ == "__main__":
    main()
