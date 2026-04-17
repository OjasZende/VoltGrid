import osmnx as ox
import h3
import geopandas as gpd
from shapely.geometry import Polygon
from collections import defaultdict

# OSM tags used to identify Points of Interest that generate EV charging demand
POI_TAGS = {
    'landuse':        ['retail', 'commercial'],
    'public_transport': ['stop_position', 'platform'],
    'highway':        'bus_stop',
    'railway':        ['station', 'halt', 'tram_stop'],
}

def extract_spatial_data(graph_path):
    """
    Load the road graph, extract candidate sites (parking/fuel) and H3
    demand points, then weight each demand point by the number of nearby
    POIs (retail, commercial, transit) that fall inside its hexagon.

    Returns
    -------
    candidate_sites : list of (lat, lon)
    demand_points   : list of (lat, lon)   — hex centres, res-9
    demand_weights  : dict  {demand_index: int}  — POI count per hex
    """
    print(f"Loading graph from {graph_path}...")
    G = ox.load_graphml(graph_path)

    gdf_nodes, _ = ox.graph_to_gdfs(G)
    west, south, east, north = gdf_nodes.total_bounds
    bbox = (west, south, east, north)   # (left, bottom, right, top) for OSMnx 2.x
    print(f"Graph bounds: N={north:.5f}  S={south:.5f}  E={east:.5f}  W={west:.5f}")

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

    print("Generating H3 demand points at resolution 9...")
    cells = h3.polygon_to_cells(h3.LatLngPoly(poly_coords), res=9)
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
            cell = h3.latlng_to_cell(geom.y, geom.x, 9)
            poi_counts[cell] += 1

    # Build demand_weights for every demand hex (default = 0 if no POIs)
    demand_weights = {
        cell_to_idx[c]: poi_counts.get(c, 0)
        for c in cell_list
    }

    total_weighted = sum(1 for w in demand_weights.values() if w > 0)
    print(f"  -> {len(pois) if not pois.empty else 0} POIs found.")
    print(f"  -> {total_weighted} / {len(demand_points)} demand hexagons have at least 1 POI.")

    return candidate_sites, demand_points, demand_weights


if __name__ == "__main__":
    graph_file = "data/mumbai_network.graphml"
    candidate_sites, demand_points, demand_weights = extract_spatial_data(graph_file)

    print("\nSample Candidate Sites (Lat, Lon):")
    for site in candidate_sites[:5]:
        print(f"  {site}")

    print("\nSample Demand Points with Weights (index, lat, lon, weight):")
    for i, pt in enumerate(demand_points[:10]):
        print(f"  [{i}]  {pt}  ->  weight={demand_weights[i]}")
