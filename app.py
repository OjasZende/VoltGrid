import sys
import os
import h3
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add backend/algo to path so local imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "algo"))
# Add driver_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "driver_app"))

from extraction_script import extract_spatial_data
from distance_matrix import calculate_distance_matrix
from set_cover_optimizer import solve_mclp
from route_feasibility import check_feasibility

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
    # Base load (use_ai=False to get raw POIs initially, but we'll re-run as needed)
    candidate_sites, demand_points, demand_weights, substations = extract_spatial_data(GRAPH_FILE, use_ai=False)
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
def get_spatial_data(use_ai: bool = Query(True)):
    """Returns candidate sites, hex boundaries, and weights (AI-adjusted if use_ai=True)."""
    weights = global_demand_weights
    if use_ai:
        # Re-run extraction with AI enabled
        # In a real app we'd cache this, but for the demo we'll just call it
        _, _, weights, _ = extract_spatial_data(GRAPH_FILE, use_ai=True)
    
    max_w = max(weights.values()) if weights else 1
    
    # Baseline comparison (POI-only) for the UI stats
    _, _, base_weights, _ = extract_spatial_data(GRAPH_FILE, use_ai=False)
    base_total = sum(base_weights.values())

    return {
        "candidateSites": global_candidate_sites,
        "demandPoints": global_demand_points,
        "demandWeights": weights,
        "hexPolys": global_hex_polys,
        "maxWeight": max_w,
        "baseTotalWeight": base_total,
        "is_ai": use_ai
    }

@app.get("/api/optimize")
def run_optimization(k: int = Query(10, ge=1, le=50), use_ai: bool = Query(True)):
    """Runs the MCLP optimization with the given budget K and AI toggle."""
    weights = global_demand_weights
    if use_ai:
        _, _, weights, _ = extract_spatial_data(GRAPH_FILE, use_ai=True)

    selected_sites = solve_mclp(
        global_candidate_sites,
        global_demand_points,
        weights,
        global_reachability,
        K=k,
        substations=global_substations
    )

    # Calculate metrics
    selected_set = set(map(tuple, selected_sites))
    total_weight = sum(weights.values())
    
    covered_weight = sum(
        weights.get(i, 0)
        for i, site in enumerate(global_demand_points)
        if global_reachability.get(i, []) and
           any(tuple(global_candidate_sites[j]) in selected_set for j in global_reachability.get(i, []))
    )

    # Baseline comparison (POI-only) for the UI stats
    # We'll return this to show "AI Boost" in the React UI
    _, _, base_weights, _ = extract_spatial_data(GRAPH_FILE, use_ai=False)
    base_total = sum(base_weights.values())
    
    # Dead zone count (demand > 10 and not covered)
    dead_zones = sum(1 for i, w in weights.items() if w > 10 and not (
        global_reachability.get(i, []) and
        any(tuple(global_candidate_sites[j]) in selected_set for j in global_reachability.get(i, []))
    ))

    return {
        "selectedSites": selected_sites,
        "coveredWeight": covered_weight,
        "totalWeight": total_weight,
        "deadZones": dead_zones,
        "baseTotalWeight": base_total,
        "is_ai": use_ai
    }

# ── Driver App endpoints ────────────────────────────────────────────────────

class RouteCheckRequest(BaseModel):
    battery_pct: float          # 0-100
    vehicle_range_km: float     # total range at 100%
    origin: str                 # free-text address or "lat,lon"
    destination: str            # free-text address or "lat,lon"
    strategy: str = "full"      # "full" or "min"
    use_ai: bool = True         # Toggle AI queue prediction

@app.post("/api/route-check")
def route_check(req: RouteCheckRequest):
    """
    Check if an EV can reach its destination on current battery.
    Returns feasibility result + geocoded coords + OSRM road geometry for map display.
    """
    from route_feasibility import _geocode, _osrm_route_geometry
    import time as _time

    # Step 0: Get the active station network for this request
    stations_data = get_stations(use_ai=req.use_ai)
    stations_list = stations_data.get("stations", [])

    result = check_feasibility(
        user_battery_pct=req.battery_pct,
        vehicle_range=req.vehicle_range_km,
        origin_address=req.origin,
        destination_address=req.destination,
        strategy=req.strategy,
        use_ai=req.use_ai,
        stations=stations_list,
    )

    # Geocode both ends
    try:
        orig_lat, orig_lon = _geocode(req.origin)
        _time.sleep(1)
        dest_lat, dest_lon = _geocode(req.destination)
        result["origin_coords"] = [orig_lat, orig_lon]
        result["dest_coords"] = [dest_lat, dest_lon]

        # Fetch actual OSRM road geometry for drawing on map
        if result.get("feasible"):
            # Direct route
            geom = _osrm_route_geometry(orig_lat, orig_lon, dest_lat, dest_lon)
            result["route_geometry"] = geom
        elif result.get("recommendation") and result["recommendation"].get("station"):
            s = result["recommendation"]["station"]
            # Leg 1: Origin -> Station
            leg1 = _osrm_route_geometry(orig_lat, orig_lon, s["lat"], s["lon"])
            # Leg 2: Station -> Destination
            leg2 = _osrm_route_geometry(s["lat"], s["lon"], dest_lat, dest_lon)
            result["leg1_geometry"] = leg1
            result["leg2_geometry"] = leg2

    except Exception as e:
        print(f"Geometry fetch error: {e}")

    return result

@app.get("/api/stations")
def get_stations(use_ai: bool = Query(True), k: int = Query(15)):
    """
    Returns the VoltGrid station list.
    If use_ai/k are provided, it runs a live optimization to show the AI-optimized network.
    """
    try:
        # Re-run optimization to get the "active" network for the driver
        # Use the cached spatial data from app startup
        weights = global_demand_weights
        if use_ai:
            _, _, weights, _ = extract_spatial_data(GRAPH_FILE, use_ai=True)

        selected_sites = solve_mclp(
            global_candidate_sites,
            global_demand_points,
            weights,
            global_reachability,
            K=k,
            substations=global_substations
        )
        
        # Convert to the list format expected by Driver App
        stations = []
        for i, site in enumerate(selected_sites):
            stations.append({
                "id": i + 1,
                "name": f"VoltGrid Node {i+1}",
                "lat": site[0],
                "lon": site[1],
                "type": "DC Fast",
                "status": "online"
            })
        return {"stations": stations, "is_ai": use_ai}

    except Exception as e:
        print(f"Dynamic stations error: {e}")
        # Fallback to static stations.json if optimization fails
        import json
        stations_file = os.path.join(os.path.dirname(__file__), "driver_app", "stations.json")
        if not os.path.exists(stations_file):
            return {"stations": [], "error": "stations.json not found."}
        with open(stations_file) as f:
            return {"stations": json.load(f)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
