import osmnx as ox
import h3
import inspect

print(f"OSMnx version: {ox.__version__}")
print(f"H3 version: {h3.__version__}")

print("\nOSMnx features_from_bbox signature:")
try:
    print(inspect.signature(ox.features_from_bbox))
except Exception as e:
    print(e)

print("\nH3 attributes matching 'Poly':")
print([a for a in dir(h3) if 'Poly' in a])

print("\nH3 attributes matching 'cell' or 'polygon':")
print([a for a in dir(h3) if 'cell' in a or 'poly' in a])
