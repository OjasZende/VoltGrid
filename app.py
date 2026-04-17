import sys
import os
import h3
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add backend/algo to path so local imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "algo"))
from extraction_script import extract_spatial_data
from distance_matrix import calculate_distance_matrix
from set_cover_optimizer import solve_mclp

app = FastAPI(title="VoltGrid API")

# Allow CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GRAPH_FILE = os.path.join(os.path.dirname(__file__), "data", "mumbai_network.graphml")

# Global variables to hold cached spatial data
global_candidate_sites = None
global_demand_points = None
global_demand_weights = None
global_reachability = None
global_hex_polys = None
global_substations = None
global_max_w = 1

def load_spatial_data():
    global global_candidate_sites, global_demand_points, global_demand_weights
    global global_reachability, global_hex_polys, global_max_w, global_substations

    if global_candidate_sites is not None:
        return  # Already loaded

    print("Loading spatial data and calculating distance matrix...")
    candidate_sites, demand_points, demand_weights, substations = extract_spatial_data(GRAPH_FILE)
    reachability = calculate_distance_matrix(GRAPH_FILE, demand_points, candidate_sites)

    # Pre-build hex boundary polygons for the map layer
    hex_polys = []
    for dp in demand_points:
        cell = h3.latlng_to_cell(dp[0], dp[1], 9)
        boundary = h3.cell_to_boundary(cell)
        hex_polys.append(list(boundary))

    global_candidate_sites = candidate_sites
    global_demand_points = demand_points
    global_demand_weights = demand_weights
    global_reachability = reachability
    global_hex_polys = hex_polys
    global_substations = substations
    if demand_weights:
        global_max_w = max(demand_weights.values())
    print("Data loaded successfully.")

@app.on_event("startup")
async def startup_event():
    # Load spatial data on startup so it doesn't block the first request
    # Note: If it takes too long, we can do it in a background thread,
    # but for local dev, blocking startup is fine.
    load_spatial_data()

@app.get("/api/spatial-data")
def get_spatial_data():
    """Returns candidate sites, hex boundaries, and weights."""
    return {
        "candidateSites": global_candidate_sites,
        "demandPoints": global_demand_points,
        "demandWeights": global_demand_weights,
        "hexPolys": global_hex_polys,
        "maxWeight": global_max_w
    }

@app.get("/api/optimize")
def run_optimization(k: int = Query(10, ge=1, le=50)):
    """Runs the MCLP optimization with the given budget K."""
    selected_sites = solve_mclp(
        global_candidate_sites,
        global_demand_points,
        global_demand_weights,
        global_reachability,
        K=k,
        substations=global_substations
    )

    # Calculate covered weight
    selected_set = set(map(tuple, selected_sites))
    total_weight = sum(global_demand_weights.values())
    
    covered_weight = sum(
        global_demand_weights.get(i, 0)
        for i, site in enumerate(global_demand_points)
        if global_reachability.get(i, []) and
           any(tuple(global_candidate_sites[j]) in selected_set for j in global_reachability.get(i, []))
    )

    return {
        "selectedSites": selected_sites,
        "coveredWeight": covered_weight,
        "totalWeight": total_weight
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
