# Region Modes: "core_mumbai" or "greater_mumbai"
REGION_MODE = "greater_mumbai"

if REGION_MODE == "greater_mumbai":
    # Bounding Box: West, South, East, North
    BOUNDS = (72.74, 18.88, 73.08, 19.33)
    H3_RESOLUTION = 8
    GRAPH_FILE_NAME = "greater_mumbai_network.graphml"
    REGION_NAME = "Greater Mumbai"
else:
    # Core Mumbai (Colaba to Bandra/Kurla)
    BOUNDS = (72.80, 18.90, 72.95, 19.15)
    H3_RESOLUTION = 9
    GRAPH_FILE_NAME = "mumbai_network.graphml"
    REGION_NAME = "Core Mumbai"

GREATER_MUMBAI_GRAPH = f"data/{GRAPH_FILE_NAME}"
