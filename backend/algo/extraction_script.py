import osmnx as ox
import h3
import geopandas as gpd
from shapely.geometry import Polygon
from collections import defaultdict
import sys
import datetime
import pandas as pd
import os
try:
    from spatial_config import BOUNDS, H3_RESOLUTION
    USE_CONFIG_BOUNDS = True
except ImportError:
    USE_CONFIG_BOUNDS = False
    H3_RESOLUTION = 9

# Add src to path to import ml
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
# OSM tags used to identify Points of Interest that generate EV charging demand
POI_TAGS = {
    'landuse':        ['retail', 'commercial'],
    'public_transport': ['stop_position', 'platform'],
    'highway':        'bus_stop',
    'railway':        ['station', 'halt', 'tram_stop'],
}

# ML Toggle
DEFAULT_USE_AI = True

def extract_spatial_data(graph_or_path, use_ai=DEFAULT_USE_AI):
    """
    ... (docstring) ...
    """
    if isinstance(graph_or_path, str):
        print(f"Loading graph from {graph_or_path}...")
        G = ox.load_graphml(graph_or_path)
    else:
        G = graph_or_path

    gdf_nodes, _ = ox.graph_to_gdfs(G)
    west, south, east, north = gdf_nodes.total_bounds
    
    if USE_CONFIG_BOUNDS:
        west, south, east, north = BOUNDS
        print(f"Using Greater Mumbai Bounds: N={north:.5f} S={south:.5f} E={east:.5f} W={west:.5f}")
    else:
        print(f"Graph bounds: N={north:.5f}  S={south:.5f}  E={east:.5f}  W={west:.5f}")
    
    bbox = (west, south, east, north)   # (left, bottom, right, top) for OSMnx 2.x

    # ── 1. Candidate sites: parking & fuel amenities ──────────────────────────
    print("Fetching candidate sites (parking / fuel) from OSM...")
    try:
        features = ox.features_from_bbox(bbox=bbox, tags={'amenity': ['parking', 'fuel']})
    except Exception as e:
        print(f"  Warning – candidate fetch failed: {e}")
        features = gpd.GeoDataFrame()

    candidate_sites = []
    if not features.empty:
        centroids = features.geometry.to_crs("EPSG:4326").centroid
        candidate_sites = list(zip(centroids.y, centroids.x))
    print(f"  -> {len(candidate_sites)} candidate sites extracted.")

    # ── 2. H3 demand points (resolution 9) ───────────────────────────────────
    bbox_poly   = Polygon([(west, south), (east, south), (east, north), (west, north)])
    poly_coords = [(lat, lon) for lon, lat in bbox_poly.exterior.coords]

    print(f"Generating H3 demand points at resolution {H3_RESOLUTION}...")
    cells = h3.polygon_to_cells(h3.LatLngPoly(poly_coords), res=H3_RESOLUTION)
    # Map cell id → demand index (stable ordering)
    cell_list    = list(cells)
    demand_points = [h3.cell_to_latlng(c) for c in cell_list]
    cell_to_idx  = {c: i for i, c in enumerate(cell_list)}
    print(f"  -> {len(demand_points)} demand points generated.")

    # ── 3. POI extraction: retail, commercial, transit ────────────────────────
    print("Fetching POIs (retail / commercial / transit) from OSM...")
    try:
        pois = ox.features_from_bbox(bbox=bbox, tags=POI_TAGS)
    except Exception as e:
        print(f"  Warning – POI fetch failed: {e}")
        pois = gpd.GeoDataFrame()

    # ── 4. Weight each demand hex by POI count ────────────────────────────────
    # For every POI centroid, find which res-9 hex it belongs to and tally.
    poi_counts = defaultdict(int)   # cell_id → count

    if not pois.empty:
        poi_centroids = pois.geometry.centroid
        for geom in poi_centroids:
            if geom is None or geom.is_empty:
                continue
            cell = h3.latlng_to_cell(geom.y, geom.x, H3_RESOLUTION)
            poi_counts[cell] += 1

    # Build demand_weights for every demand hex (default = 0 if no POIs)
    demand_weights = {
        cell_to_idx[c]: poi_counts.get(c, 0)
        for c in cell_list
    }

    # ML: demand prediction
    if use_ai:
        try:
            from src.ml.predict import predict_demand
            print("  Applying ML Demand Prediction to zones...")
            
            # Prepare dataframe for prediction
            current_hour = datetime.datetime.now().hour
            current_day = datetime.datetime.now().weekday()
            
            # Create synthetic feature values based on the schema
            # hour, day_of_week, traffic_score, parking_density, grid_capacity, existing_station_count, ev_registrations
            records = []
            for i, cell in enumerate(cell_list):
                poi_c = poi_counts.get(cell, 0)
                records.append({
                    'hour': current_hour,
                    'day_of_week': current_day,
                    'traffic_score': min(100, poi_c * 10),       # proxy
                    'parking_density': min(1.0, poi_c * 0.1),    # proxy
                    'grid_capacity': 250,                        # static proxy
                    'existing_station_count': 1,                 # static proxy
                    'ev_registrations': 40000                    # static proxy
                })
                
            df = pd.DataFrame(records)
            predicted_scores = predict_demand(df)
            
            # Replace raw demand weights with ML predicted scores
            for i, score in enumerate(predicted_scores):
                # Ensure it's a positive float or int
                demand_weights[i] = max(0.0, float(score))
                
            print(f"  -> ML predictions successfully applied to {len(demand_weights)} zones.")
        except Exception as e:
            print(f"  Warning: ML Demand Prediction failed ({e}). Falling back to raw POI weights.")

    total_weighted = sum(1 for w in demand_weights.values() if w > 0)
    print(f"  -> {len(pois) if not pois.empty else 0} POIs found.")
    print(f"  -> {total_weighted} / {len(demand_points)} demand hexagons have at least 1 POI.")

    # -- 5. Electrical substations (grid congestion constraint) ----------------
    print("Fetching electrical substations from OSM...")
    try:
        subs = ox.features_from_bbox(
            bbox=bbox,
            tags={"power": ["substation", "sub_station"]}
        )
    except Exception as e:
        print(f"  Warning - substation fetch failed: {e}")
        subs = gpd.GeoDataFrame()

    substations = []
    if not subs.empty:
        sub_centroids = subs.geometry.centroid
        substations = list(zip(sub_centroids.y, sub_centroids.x))
    print(f"  -> {len(substations)} substations found.")

    return candidate_sites, demand_points, demand_weights, substations


if __name__ == "__main__":
    graph_file = "data/mumbai_network.graphml"
    candidate_sites, demand_points, demand_weights, substations = extract_spatial_data(graph_file)

    print("\nSample Candidate Sites (Lat, Lon):")
    for site in candidate_sites[:5]:
        print(f"  {site}")

    print("\nSample Demand Points with Weights (index, lat, lon, weight):")
    for i, pt in enumerate(demand_points[:10]):
        print(f"  [{i}]  {pt}  ->  weight={demand_weights[i]}")

    print("\nSubstations (Lat, Lon):")
    for s in substations:
        print(f"  {s}")
