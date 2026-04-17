"""
Generate stations.json by running the full MCLP pipeline and saving
the selected station coordinates so route_feasibility.py can import them.

Run once from the project root:
    python driver_app/generate_stations.py
"""
import sys, os, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "algo"))

from extraction_script import extract_spatial_data
from distance_matrix import calculate_distance_matrix
from set_cover_optimizer import solve_mclp

GRAPH_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "mumbai_network.graphml")
OUT_FILE   = os.path.join(os.path.dirname(__file__), "stations.json")

# ── Budget K — change this to match what you use in the Streamlit app ─────────
K = 10

def main():
    print("Running MCLP pipeline to generate stations.json ...")

    candidate_sites, demand_points, demand_weights, substations = \
        extract_spatial_data(GRAPH_FILE)
    reachability    = calculate_distance_matrix(GRAPH_FILE, demand_points, candidate_sites)
    selected_coords = solve_mclp(candidate_sites, demand_points, demand_weights,
                                  reachability, K=K, substations=substations)

    stations = [
        {
            "id":   i + 1,
            "name": f"VoltGrid Station {i + 1}",
            "lat":  coord[0],
            "lon":  coord[1]
        }
        for i, coord in enumerate(selected_coords)
    ]

    with open(OUT_FILE, "w") as f:
        json.dump(stations, f, indent=2)

    print(f"\nSaved {len(stations)} stations to: {OUT_FILE}")
    for s in stations:
        print(f"  [{s['id']:>2}] {s['name']}  ({s['lat']:.6f}, {s['lon']:.6f})")

if __name__ == "__main__":
    main()
