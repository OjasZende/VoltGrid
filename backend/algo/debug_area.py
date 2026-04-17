import osmnx as ox
from shapely.geometry import box
import geopandas as gpd

north, south, east, west = 19.0876425, 19.0336908, 72.8831997, 72.8261429
bbox_poly = box(west, south, east, north)
gdf = gpd.GeoDataFrame({'geometry': [bbox_poly]}, crs="EPSG:4326")
gdf_proj = ox.projection.project_gdf(gdf)
area = gdf_proj.geometry.iloc[0].area
print(f"Area in sq meters: {area}")
print(f"Current max_query_area_size: {ox.settings.max_query_area_size}")
