import sys
import os
import streamlit as st
import folium
import h3
from streamlit_folium import st_folium

# ── Add backend/algo to path so local imports work ──────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "algo"))
from extraction_script import extract_spatial_data
from distance_matrix import calculate_distance_matrix
from set_cover_optimizer import solve_mclp

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="VoltGrid – Mumbai EV Optimizer", layout="wide")
st.title("⚡ VoltGrid: Mumbai EV Station Optimizer")
st.caption("MCLP optimisation over the Mumbai road network — maximise weighted POI demand coverage within a station budget.")

GRAPH_FILE = os.path.join(os.path.dirname(__file__), "data", "mumbai_network.graphml")

# ── Sidebar controls ─────────────────────────────────────────────────────────
st.sidebar.title("Optimiser Settings")
K             = st.sidebar.slider("Station Budget (K)", min_value=1, max_value=30, value=10, step=1,
                                   help="Maximum number of EV stations to place")
radius        = st.sidebar.slider("Coverage Radius (m)", 500, 5000, 2000, step=100,
                                   help="Driving distance threshold for a demand point to be 'covered'")
show_hexagons = st.sidebar.checkbox("Show Demand Grid (H3 hexagons)", value=True)
show_weights  = st.sidebar.checkbox("Colour hexagons by POI weight", value=True)

st.sidebar.divider()
st.sidebar.markdown("**Legend**")
st.sidebar.markdown("🔴 Existing site (unoptimised)")
st.sidebar.markdown("🟢 Selected MCLP station")
st.sidebar.markdown("⚫ Unselected candidate")
st.sidebar.markdown("⬡ H3 demand hex (shaded = higher POI weight)")

# ── Heavy computation — cache spatial data & distance matrix separately ───────
@st.cache_data(show_spinner="Extracting spatial data & POI weights…")
def load_spatial(graph_file):
    candidate_sites, demand_points, demand_weights = extract_spatial_data(graph_file)
    reachability = calculate_distance_matrix(graph_file, demand_points, candidate_sites)

    # Pre-build hex boundary polygons for the map layer
    hex_polys = []
    for dp in demand_points:
        cell     = h3.latlng_to_cell(dp[0], dp[1], 9)
        boundary = h3.cell_to_boundary(cell)
        hex_polys.append(list(boundary))

    return candidate_sites, demand_points, demand_weights, reachability, hex_polys

@st.cache_data(show_spinner="Solving MCLP…")
def run_mclp(graph_file, K):
    candidate_sites, demand_points, demand_weights, reachability, hex_polys = load_spatial(graph_file)
    selected_sites = solve_mclp(candidate_sites, demand_points, demand_weights, reachability, K=K)
    return selected_sites

candidate_sites, demand_points, demand_weights, reachability, hex_polys = load_spatial(GRAPH_FILE)
selected_sites = run_mclp(GRAPH_FILE, K)

selected_set  = set(map(tuple, selected_sites))
total_weight  = sum(demand_weights.values())
max_w         = max(demand_weights.values()) if demand_weights else 1

# Weight covered = demand points whose hex has weight > 0 AND are covered by a selected station
covered_weight = sum(
    demand_weights.get(i, 0)
    for i, site in enumerate(demand_points)
    if reachability.get(i, []) and
       any(tuple(candidate_sites[j]) in selected_set for j in reachability.get(i, []))
)

# ── Top-level metrics ─────────────────────────────────────────────────────────
st.markdown("### 📊 Summary")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("H3 Demand Points", len(demand_points))
m2.metric("Candidate Sites", len(candidate_sites))
m3.metric("Station Budget (K)", K)
m4.metric("Stations Placed", len(selected_sites))
m5.metric("POI Weight Covered",
          f"{covered_weight} / {total_weight}",
          delta=f"{100*covered_weight/total_weight:.1f}%" if total_weight else "N/A")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_before, tab_after = st.tabs(["🔴 Before — All Existing Sites", "🟢 After — MCLP Optimised Placement"])

CENTER  = [19.0760, 72.8777]
ZOOM    = 13
BASEMAP = "cartodb positron"


def weight_to_color(weight, max_weight):
    """Map a POI weight to a hex colour: grey (0 POIs) → deep orange (many POIs)."""
    if max_weight == 0 or weight == 0:
        return "#dee2e6", 0.1     # light grey, near transparent
    ratio = min(weight / max_weight, 1.0)
    # Interpolate from light yellow → deep orange-red
    r = int(255)
    g = int(200 - ratio * 160)
    b = int(50  - ratio * 50)
    return f"#{r:02x}{g:02x}{b:02x}", 0.15 + ratio * 0.5


def add_hex_grid(fmap):
    if not show_hexagons:
        return
    hex_group = folium.FeatureGroup(name="Demand Grid")
    for i, boundary in enumerate(hex_polys):
        w         = demand_weights.get(i, 0)
        color, opacity = weight_to_color(w, max_w) if show_weights else ("#adb5bd", 0.15)
        folium.Polygon(
            locations=boundary,
            color="#6c757d", weight=0.5,
            fill=True, fill_color=color, fill_opacity=opacity,
            tooltip=f"Hex {i} — POI weight: {w}"
        ).add_to(hex_group)
    hex_group.add_to(fmap)


# ── BEFORE tab ────────────────────────────────────────────────────────────────
with tab_before:
    st.markdown(
        f"All **{len(candidate_sites)} existing OSM parking / fuel amenity sites** — unoptimised distribution. "
        "Hexagon colour intensity reflects the number of nearby retail, commercial and transit POIs."
    )

    m_before = folium.Map(location=CENTER, zoom_start=ZOOM, tiles=BASEMAP)
    add_hex_grid(m_before)

    before_group = folium.FeatureGroup(name="Existing Sites")
    for i, site in enumerate(candidate_sites):
        folium.CircleMarker(
            location=site, radius=7,
            color="#dc3545", fill=True, fill_color="#dc3545", fill_opacity=0.8,
            tooltip=f"Existing site {i}: ({site[0]:.5f}, {site[1]:.5f})"
        ).add_to(before_group)
    before_group.add_to(m_before)

    folium.LayerControl().add_to(m_before)
    st_folium(m_before, width="100%", height=580, key="map_before")


# ── AFTER tab ────────────────────────────────────────────────────────────────
with tab_after:
    st.markdown(
        f"**{len(selected_sites)} MCLP-optimal stations** (budget K={K}) maximising POI-weighted demand coverage "
        f"within **{radius} m** driving distance. "
        f"Covered weight: **{covered_weight} / {total_weight}** "
        f"({100*covered_weight/total_weight:.1f}%)." if total_weight else ""
    )

    col_map, col_list = st.columns([3, 1])

    with col_map:
        m_after = folium.Map(location=CENTER, zoom_start=ZOOM, tiles=BASEMAP)
        add_hex_grid(m_after)

        # Dim unselected candidates
        dim_group = folium.FeatureGroup(name="Unselected Candidates")
        for i, site in enumerate(candidate_sites):
            if tuple(site) not in selected_set:
                folium.CircleMarker(
                    location=site, radius=4,
                    color="#6c757d", fill=True, fill_color="#adb5bd", fill_opacity=0.4,
                    tooltip=f"Candidate {i} (not selected)"
                ).add_to(dim_group)
        dim_group.add_to(m_after)

        # Selected stations with coverage rings
        sel_group = folium.FeatureGroup(name="MCLP Stations")
        for i, site in enumerate(selected_sites):
            folium.Marker(
                location=site,
                icon=folium.Icon(color="green", icon="bolt", prefix="fa"),
                tooltip=f"Station {i+1}: ({site[0]:.5f}, {site[1]:.5f})"
            ).add_to(sel_group)
            folium.Circle(
                location=site, radius=radius,
                color="#28a745", weight=1.5,
                fill=True, fill_color="#28a745", fill_opacity=0.08
            ).add_to(sel_group)
        sel_group.add_to(m_after)

        folium.LayerControl().add_to(m_after)
        st_folium(m_after, width="100%", height=580, key="map_after")

    with col_list:
        st.markdown(f"#### Stations ({len(selected_sites)}/{K})")
        for i, site in enumerate(selected_sites):
            st.markdown(f"**#{i+1}**  \n`{site[0]:.5f}, {site[1]:.5f}`")
