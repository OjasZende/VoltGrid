"""
route_feasibility.py
────────────────────
Trip feasibility checker for EV drivers in Mumbai.

Uses FREE services only — no billing required:
  - Nominatim (OSM geocoder) to convert addresses to coordinates
  - OSRM public server (osrm-routed) for real driving distances

Given the driver's current battery percentage and vehicle range, this module:
  1. Geocodes origin and destination using Nominatim.
  2. Checks whether available battery range is sufficient (with 10% safety buffer).
  3. If not, iterates over VoltGrid optimized stations and recommends the one
     that adds the smallest detour to the trip.

Usage (CLI):
    python route_feasibility.py \
        --battery 15 \
        --range 300 \
        --origin "Andheri West, Mumbai" \
        --destination "Bandra Kurla Complex, Mumbai"

Usage (as a module):
    from route_feasibility import check_feasibility
    result = check_feasibility(
        user_battery_pct=15,
        vehicle_range=300,
        origin_address="Andheri West, Mumbai",
        destination_address="Bandra Kurla Complex, Mumbai",
    )
    print(result["message"])
"""

import json
import os
import time
import argparse
import requests
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STATIONS_FILE         = os.path.join(os.path.dirname(__file__), "stations.json")
SAFETY_BUFFER         = 0.10    # 10% safety margin on top of destination distance
MUMBAI_DEFAULT_ORIGIN = "Mumbai, Maharashtra, India"

# Charging Assumptions (Standard EV & DC Fast Charger)
CHARGING_SPEED_KW   = 50    # kW
DEFAULT_BATTERY_KWH = 60    # kWh

# Free OSRM public demo server (OpenStreetMap routing — no API key needed)
OSRM_BASE = "http://router.project-osrm.org/route/v1/driving"

# Nominatim geocoder (OSM — no API key needed, 1 request/sec rate limit)
NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"
NOMINATIM_HEADERS = {"User-Agent": "VoltGrid-EV-Planner/1.0"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_stations() -> list[dict]:
    """Load optimised station list from stations.json."""
    if not os.path.exists(STATIONS_FILE):
        raise FileNotFoundError(
            f"stations.json not found at {STATIONS_FILE}. "
            "Run driver_app/generate_stations.py first."
        )
    with open(STATIONS_FILE) as f:
        return json.load(f)


# In-memory cache so the same address is never geocoded twice (avoids 429 rate-limit)
_geocode_cache: dict = {}

# Hardcoded coordinates for common Mumbai locations — no Nominatim call needed
_MUMBAI_KNOWN: dict = {
    "andheri west, mumbai":            (19.11725, 72.83397),
    "andheri west":                    (19.11725, 72.83397),
    "andheri east, mumbai":            (19.11501, 72.87159),
    "bandra kurla complex, mumbai":    (19.05927, 72.86133),
    "bandra kurla complex":            (19.05927, 72.86133),
    "bkc, mumbai":                     (19.05927, 72.86133),
    "bandra west, mumbai":             (19.05463, 72.83945),
    "bandra, mumbai":                  (19.05463, 72.83945),
    "lower parel, mumbai":             (18.99709, 72.83147),
    "dadar, mumbai":                   (19.01769, 72.84389),
    "worli, mumbai":                   (19.00693, 72.81813),
    "nariman point, mumbai":           (18.92546, 72.82127),
    "colaba, mumbai":                  (18.90614, 72.82044),
    "borivali, mumbai":                (19.22857, 72.85736),
    "malad, mumbai":                   (19.18711, 72.84848),
    "goregaon, mumbai":                (19.15548, 72.84890),
    "powai, mumbai":                   (19.12002, 72.90499),
    "thane, mumbai":                   (19.21782, 72.97820),
    "kurla, mumbai":                   (19.07060, 72.88145),
    "chembur, mumbai":                 (19.06164, 72.89873),
    "vikhroli, mumbai":                (19.10508, 72.92540),
    "mulund, mumbai":                  (19.17660, 72.95683),
    "mumbai central, mumbai":          (18.96950, 72.82026),
    "cst, mumbai":                     (18.93974, 72.83511),
    "fort, mumbai":                    (18.93305, 72.83553),
    "marine lines, mumbai":            (18.94411, 72.82294),
    "juhu, mumbai":                    (19.10289, 72.82662),
    "versova, mumbai":                 (19.12720, 72.81398),
    "santacruz, mumbai":               (19.08078, 72.84505),
    "vile parle, mumbai":              (19.09910, 72.84913),
    "khar, mumbai":                    (19.07050, 72.83632),
    "sion, mumbai":                    (19.03960, 72.86040),
    "matunga, mumbai":                 (19.02779, 72.85491),
    "ghatkopar, mumbai":               (19.08743, 72.91019),
    "mumbai, maharashtra, india":      (19.07283, 72.88261),
    "mumbai":                          (19.07283, 72.88261),
}


def _geocode(address: str) -> tuple[float, float]:
    """
    Convert a free-text address string to (lat, lon).

    Priority:
      1. Direct lat,lon string passthrough
      2. Hardcoded Mumbai lookup table (no network call)
      3. In-memory cache (no duplicate Nominatim calls)
      4. Nominatim OSM geocoder (with 429 protection)
    """
    # 1. Direct lat,lon passthrough
    parts = address.split(",")
    if len(parts) == 2:
        try:
            return float(parts[0].strip()), float(parts[1].strip())
        except ValueError:
            pass

    key = address.strip().lower()

    # 2. Hardcoded lookup
    if key in _MUMBAI_KNOWN:
        return _MUMBAI_KNOWN[key]

    # 3. Memory cache
    if key in _geocode_cache:
        return _geocode_cache[key]

    # 4. Nominatim (rate-limited — use sparingly)
    params = {
        "q":      address,
        "format": "json",
        "limit":  1,
    }
    try:
        resp = requests.get(NOMINATIM_BASE, params=params,
                            headers=NOMINATIM_HEADERS, timeout=10)
        if resp.status_code == 429:
            raise ValueError(
                "Nominatim geocoder is temporarily rate-limited. "
                "Please use a specific address like 'Andheri West, Mumbai' "
                "or enter coordinates as 'lat,lon' directly."
            )
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise ValueError(f"Geocoding timed out for '{address}'. Try again shortly.")

    results = resp.json()
    if not results:
        raise ValueError(
            f"Could not geocode '{address}'. "
            "Try a more specific address, e.g. 'Andheri West, Mumbai, India'."
        )

    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    _geocode_cache[key] = (lat, lon)
    return lat, lon


def _osrm_distance_km(lat1: float, lon1: float,
                       lat2: float, lon2: float) -> float:
    """
    Return the driving distance in km between two (lat, lon) points using
    the free OSRM public server. No API key required.

    OSRM coordinate order is lon,lat (GeoJSON convention).
    """
    url = f"{OSRM_BASE}/{lon1},{lat1};{lon2},{lat2}"
    params = {"overview": "false", "annotations": "false"}

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError(
            f"OSRM returned no route between ({lat1},{lon1}) and ({lat2},{lon2}). "
            f"Response: {data}"
        )

    return data["routes"][0]["distance"] / 1000.0    # metres -> km


def _osrm_route_geometry(lat1: float, lon1: float,
                          lat2: float, lon2: float) -> list[list[float]]:
    """
    Fetch the actual road-snapped route geometry between two points from OSRM.

    Returns a list of [lat, lon] pairs that trace the real driving path
    (suitable for folium.PolyLine locations).

    OSRM GeoJSON coordinates are [lon, lat] — this function flips them.
    """
    url = f"{OSRM_BASE}/{lon1},{lat1};{lon2},{lat2}"
    params = {
        "overview":   "full",      # full geometry (not simplified)
        "geometries": "geojson",   # return as GeoJSON
        "annotations": "false",
    }

    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError(
            f"OSRM returned no geometry between ({lat1},{lon1}) and ({lat2},{lon2})."
        )

    # GeoJSON coords are [lon, lat] — flip to [lat, lon] for Folium
    coords = data["routes"][0]["geometry"]["coordinates"]
    return [[lat, lon] for lon, lat in coords]


# Direction icon lookup for maneuver type + modifier
_DIRECTION_ICONS = {
    ("turn",    "left"):          "Turn left",
    ("turn",    "right"):         "Turn right",
    ("turn",    "slight left"):   "Bear left",
    ("turn",    "slight right"):  "Bear right",
    ("turn",    "sharp left"):    "Sharp left",
    ("turn",    "sharp right"):   "Sharp right",
    ("turn",    "uturn"):         "U-turn",
    ("continue","straight"):      "Continue straight",
    ("new name",""):              "Continue",
    ("depart",  ""):              "Start",
    ("arrive",  ""):              "Arrive",
    ("roundabout", ""):           "Enter roundabout",
    ("exit roundabout", ""):      "Exit roundabout",
    ("merge",   ""):              "Merge",
    ("fork",    "left"):          "Take left fork",
    ("fork",    "right"):         "Take right fork",
}


def _osrm_route_steps(lat1: float, lon1: float,
                       lat2: float, lon2: float) -> list[dict]:
    """
    Fetch turn-by-turn navigation steps from OSRM between two points.

    Returns a list of step dicts:
        {
            "instruction": str,   e.g. "Turn left"
            "road":        str,   e.g. "SV Road"
            "distance_m":  float, distance of this step in metres
            "duration_s":  float, estimated duration in seconds
        }
    """
    url = f"{OSRM_BASE}/{lon1},{lat1};{lon2},{lat2}"
    params = {
        "steps":      "true",
        "overview":   "false",
        "geometries": "geojson",
        "annotations": "false",
    }

    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        return []

    steps = []
    for leg in data["routes"][0].get("legs", []):
        for step in leg.get("steps", []):
            maneuver  = step.get("maneuver", {})
            m_type    = maneuver.get("type", "")
            m_mod     = maneuver.get("modifier", "")

            # Build human-readable instruction
            label = _DIRECTION_ICONS.get(
                (m_type, m_mod),
                _DIRECTION_ICONS.get((m_type, ""), m_type.capitalize())
            )

            road = step.get("name", "").strip()
            if road:
                instruction = f"{label} onto {road}"
            else:
                instruction = label

            steps.append({
                "instruction": instruction,
                "road":        road,
                "distance_m":  round(step.get("distance", 0), 1),
                "duration_s":  round(step.get("duration", 0), 1),
            })

    return steps


# ---------------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------------

def check_feasibility(
    user_battery_pct: float,
    vehicle_range: float,
    destination_address: str,
    origin_address: str = MUMBAI_DEFAULT_ORIGIN,
    strategy: str = "full",      # "full" or "min"
    api_key: str = "",           # kept for backwards-compat; not used
) -> dict:
    """
    Assess whether the driver can reach the destination on current battery.

    Parameters
    ----------
    user_battery_pct    : float  - current battery level (0-100)
    vehicle_range       : float  - total range at 100% battery (km)
    destination_address : str   - free-text address of destination
    origin_address      : str   - free-text address of current location
    api_key             : str   - ignored (kept for CLI compatibility)

    Returns
    -------
    dict with keys:
        feasible        : bool
        available_range : float  (km)
        dest_distance   : float  (km)
        required_range  : float  (km, with safety buffer)
        recommendation  : dict | None
        message         : str
    """
    if not (0 <= user_battery_pct <= 100):
        raise ValueError(f"battery_pct must be 0-100, got {user_battery_pct}.")

    # Step 1: Available range
    available_range = (user_battery_pct / 100.0) * vehicle_range

    # Step 2: Geocode addresses
    print(f"Geocoding '{origin_address}' ...")
    orig_lat, orig_lon = _geocode(origin_address)
    print(f"  -> ({orig_lat:.5f}, {orig_lon:.5f})")

    time.sleep(1)   # Nominatim rate limit: 1 req/sec

    print(f"Geocoding '{destination_address}' ...")
    dest_lat, dest_lon = _geocode(destination_address)
    print(f"  -> ({dest_lat:.5f}, {dest_lon:.5f})")

    # Step 3: Driving distance via OSRM
    print(f"Querying OSRM route: origin -> destination ...")
    dest_distance  = _osrm_distance_km(orig_lat, orig_lon, dest_lat, dest_lon)
    required_range = dest_distance * (1 + SAFETY_BUFFER)

    print(f"  Available range  : {available_range:.1f} km")
    print(f"  Destination dist : {dest_distance:.1f} km")
    print(f"  Required (+{SAFETY_BUFFER*100:.0f}%) : {required_range:.1f} km")

    # Step 4: Feasibility check
    if available_range >= required_range:
        msg = (
            f"Trip is feasible. You have {available_range:.1f} km of range and "
            f"the destination is {dest_distance:.1f} km away "
            f"(required with buffer: {required_range:.1f} km)."
        )
        return dict(
            feasible=True,
            available_range=available_range,
            dest_distance=dest_distance,
            required_range=required_range,
            recommendation=None,
            message=msg,
        )

    # Step 5: Re-routing — find VoltGrid station with smallest detour
    # Only stations the driver can actually REACH with current range are considered.
    print("\nInsufficient range. Evaluating VoltGrid stations for best detour ...")
    stations = _load_stations()

    best_station       = None
    best_total_km      = float("inf")
    best_detour_km     = float("inf")
    skipped_too_far    = 0

    for station in stations:
        s_lat, s_lon = station["lat"], station["lon"]
        try:
            user_to_station = _osrm_distance_km(orig_lat, orig_lon, s_lat, s_lon)

            # --- REACHABILITY GATE 1: Origin to Station ----------------------
            # Driver must be able to reach the station within available range.
            if user_to_station > available_range * (1 - SAFETY_BUFFER):
                skipped_too_far += 1
                print(f"  {station['name']:<25} : "
                      f"SKIP — station is {user_to_station:.1f} km away "
                      f"(range only {available_range:.1f} km)")
                continue

            # --- REACHABILITY GATE 2: Station to Destination -----------------
            # Driver must be able to reach destination from station assuming
            # they charge back to 100% (vehicle_range).
            station_to_dest = _osrm_distance_km(s_lat, s_lon, dest_lat, dest_lon)
            if station_to_dest > vehicle_range * (1 - SAFETY_BUFFER):
                print(f"  {station['name']:<25} : "
                      f"SKIP — destination is {station_to_dest:.1f} km from station "
                      f"(max vehicle range {vehicle_range:.1f} km)")
                continue
            # -----------------------------------------------------------------

            total_km  = user_to_station + station_to_dest
            detour_km = total_km - dest_distance

            print(f"  {station['name']:<25} : "
                  f"{user_to_station:.1f} + {station_to_dest:.1f} "
                  f"= {total_km:.1f} km  (detour +{detour_km:.1f} km)  [REACHABLE]")

            if total_km < best_total_km:
                best_total_km  = total_km
                best_detour_km = detour_km
                best_station   = station

        except Exception as e:
            print(f"  Warning: could not route via {station['name']}: {e}")

    if skipped_too_far > 0:
        print(f"\n  {skipped_too_far} station(s) skipped — out of current range.")

    if best_station is None:
        if skipped_too_far == len(stations):
            msg = (
                f"STRANDED: All {len(stations)} VoltGrid charging stations are "
                f"beyond your current range of {available_range:.1f} km. "
                "Please arrange emergency charging before departing."
            )
        else:
            msg = (
                "Insufficient range and no suitable charging station found. "
                "Please charge before departing."
            )
        return dict(
            feasible=False,
            available_range=available_range,
            dest_distance=dest_distance,
            required_range=required_range,
            recommendation=None,
            message=msg,
        )

    # Calculate charging time
    # 1. How much range do we have when we arrive at the station?
    range_on_arrival = available_range - _osrm_distance_km(orig_lat, orig_lon, best_station["lat"], best_station["lon"])
    
    # 2. How much range do we WANT to leave with?
    if strategy == "min":
        # Just enough for leg 2 + buffer
        range_target = station_to_dest * (1 + SAFETY_BUFFER)
    else:
        # Full charge
        range_target = vehicle_range
    
    # 3. How much range to add?
    range_to_add = max(0, range_target - range_on_arrival)
    
    # 4. Convert range -> kWh -> Time
    # Efficiency (km/kWh)
    efficiency = vehicle_range / DEFAULT_BATTERY_KWH
    kwh_needed = range_to_add / efficiency
    charging_time_mins = (kwh_needed / CHARGING_SPEED_KW) * 60

    msg = (
        f"Insufficient range. Recommendation: Stop at {best_station['name']}. "
        f"It is {_osrm_distance_km(orig_lat, orig_lon, best_station['lat'], best_station['lon']):.1f} km "
        f"away (within your {available_range:.1f} km range). "
        f"Charging ({strategy}) for ~{charging_time_mins:.0f} mins will allow you to complete "
        f"the remaining {station_to_dest:.1f} km of your trip."
    )

    return dict(
        feasible=False,
        available_range=available_range,
        dest_distance=dest_distance,
        required_range=required_range,
        recommendation=dict(
            station=best_station,
            total_km=best_total_km,
            detour_km=best_detour_km,
            charging_time_mins=charging_time_mins,
            strategy=strategy
        ),
        message=msg,
    )


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(description="VoltGrid Trip Feasibility Checker")
    p.add_argument("--battery",     type=float, required=True,
                   help="Current battery percentage (e.g. 15)")
    p.add_argument("--range",       type=float, required=True, dest="vehicle_range",
                   help="Vehicle range at 100%% battery in km (e.g. 300)")
    p.add_argument("--destination", type=str,   required=True,
                   help="Destination address (in quotes)")
    p.add_argument("--origin",      type=str,   default=MUMBAI_DEFAULT_ORIGIN,
                   help="Driver's current location (default: Mumbai centre)")
    p.add_argument("--api-key",     type=str,   default="",
                   help="Ignored — kept for backwards compatibility")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    result = check_feasibility(
        user_battery_pct    = args.battery,
        vehicle_range       = args.vehicle_range,
        destination_address = args.destination,
        origin_address      = args.origin,
    )

    print("\n" + "=" * 60)
    print(result["message"])
    print("=" * 60)

    if result["recommendation"]:
        rec = result["recommendation"]
        s   = rec["station"]
        print(f"\n  Station  : {s['name']}")
        print(f"  Location : ({s['lat']:.6f}, {s['lon']:.6f})")
        print(f"  Route    : {result['dest_distance']:.1f} km direct "
              f"-> {rec['total_km']:.1f} km via station")
        print(f"  Extra    : +{rec['detour_km']:.1f} km detour")
