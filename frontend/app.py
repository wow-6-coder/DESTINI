
from pathlib import Path
from datetime import time
import sys
import math

import pandas as pd
import streamlit as st
import folium
from folium.plugins import PolyLineTextPath
from streamlit_folium import st_folium


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="DESTINI | Every journey starts with a better route",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
GTFS_DIR = DATA_DIR / "static_gtfs" / "extracted"

STOPS_FILE = GTFS_DIR / "stops.txt"
SHAPES_FILE = GTFS_DIR / "shapes.txt"
TRIPS_FILE = GTFS_DIR / "trips.txt"

CONNECTIONS_FILE = DATA_DIR / "processed" / "bus_connections_enriched.csv"
GPS_FILE = DATA_DIR / "processed" / "route_764_integrated_estimates.csv"

sys.path.insert(0, str(BASE_DIR / "src" / "journey_planner"))

from raptor_engine import load_raptor_data, find_raptor_journeys


# ============================================================
# ROUTEFLOW-INSPIRED LIGHT THEME
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
:root { --navy:#142b4d; --blue:#2563eb; --ink:#172b4d; --muted:#64748b; --line:#e2e8f0; --panel:#fff; --canvas:#f3f6fb; }
html, body, [class*="css"] { font-family:Inter,system-ui,sans-serif; }
.stApp { background:var(--canvas) !important; color:var(--ink) !important; }
header[data-testid="stHeader"] { background:rgba(243,246,251,.96) !important; }
.block-container { max-width:1440px; padding:0 1.25rem 2.2rem; }
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p { color:var(--ink); }
[data-testid="stCaptionContainer"] p, .stCaption { color:var(--muted) !important; }
.destini-topbar { display:flex; align-items:center; justify-content:space-between; gap:20px; padding:16px 4px 14px; margin-bottom:18px; border-bottom:1px solid var(--line); background:#fff; }
.destini-logo { display:flex; align-items:center; gap:12px; color:var(--ink); font-size:20px; font-weight:900; letter-spacing:3px; }
.destini-logo-mark { width:46px; height:46px; border-radius:12px; display:flex; align-items:center; justify-content:center; overflow:hidden; background:#000; color:#fff; font-size:25px; }
.destini-logo-mark img { width:100%; height:100%; object-fit:contain; }
.destini-nav { display:flex; gap:25px; align-items:center; color:#596b83; font-size:13px; font-weight:650; }
.destini-nav .active { color:#2563eb; border-bottom:2px solid #2563eb; padding:15px 0 13px; }
.destini-tagline { color:#53657c; font-size:12px; }
.destini-hero { position:relative; overflow:hidden; padding:30px 34px; margin:0 0 20px; border-radius:20px; color:#fff; background:linear-gradient(110deg,#102747 0%,#1d4779 68%,#2563a6 100%); box-shadow:0 10px 25px rgba(15,45,80,.12); }
.destini-brand { color:#bfdbfe; font-size:10px; font-weight:850; letter-spacing:3px; margin-bottom:10px; }
.destini-title { color:#fff !important; font-size:clamp(28px,3.4vw,42px); line-height:1.12; font-weight:900; letter-spacing:-1px; margin:0; }
.destini-subtitle { color:#dbeafe !important; font-size:13px; margin-top:10px; max-width:610px; line-height:1.65; }
.destini-tags { margin-top:17px; }
.destini-tag { display:inline-block; margin:3px 6px 0 0; padding:6px 10px; border:1px solid #ffffff40; border-radius:30px; color:#eff6ff; font-size:10px; background:#ffffff12; }
.destini-hero-art { position:absolute; right:25px; bottom:0; width:36%; height:100%; opacity:.95; }
.section-heading { font-size:18px; font-weight:800; color:#183456 !important; margin:2px 0 10px; }
.subheading { font-size:12px; color:#64748b; }
[data-testid="stVerticalBlockBorderWrapper"] { background:#fff !important; border:1px solid var(--line) !important; border-radius:15px !important; box-shadow:0 4px 16px rgba(15,40,75,.035); }
[data-testid="stMetric"] { background:#edf3fc !important; border:1px solid #e0e9f5 !important; border-radius:12px !important; padding:15px !important; }
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p { color:#5a6e88 !important; font-size:12px !important; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] div { color:#17365d !important; font-weight:800 !important; }
input, textarea, div[data-baseweb="select"] > div { background:#fff !important; color:#17365d !important; border-color:#dce3ed !important; border-radius:9px !important; -webkit-text-fill-color:#17365d !important; }
div[data-baseweb="select"] span, div[data-baseweb="popover"] *, div[data-baseweb="menu"] * { color:#17365d !important; }
[data-testid="stForm"] { background:#fff !important; border:1px solid var(--line) !important; border-radius:15px !important; padding:18px !important; box-shadow:0 4px 16px rgba(15,40,75,.035); }
.stRadio > label { display:none !important; }
.stRadio [role="radiogroup"] { gap:9px; }
.stRadio [role="radiogroup"] > label { background:#fff !important; border:1px solid #e1e8f0 !important; border-radius:12px !important; padding:13px 15px !important; margin:0 !important; align-items:flex-start !important; }
.stRadio [role="radiogroup"] > label:has(input:checked) { border:1.5px solid #2563eb !important; box-shadow:0 0 0 1px #2563eb inset; }
.stRadio [role="radiogroup"] p, .stRadio [role="radiogroup"] span { color:#17365d !important; }
div.stButton > button, div.stFormSubmitButton > button { background:#2563eb !important; color:#fff !important; border:0 !important; border-radius:9px !important; min-height:44px; font-weight:750; }
div.stButton > button:hover, div.stFormSubmitButton > button:hover { background:#1d4ed8 !important; color:#fff !important; }
[data-testid="stAlert"] { border-radius:12px !important; }
hr { border-color:#e2e8f0 !important; }
.route-pill { display:inline-block; padding:4px 9px; border-radius:20px; background:#eaf2ff; color:#1d4ed8; font-size:10px; font-weight:800; }
.route-card-title { color:#183456; font-size:16px; font-weight:850; }
.timeline { margin:8px 0 12px 5px; border-left:2px solid #d9e5f5; padding-left:18px; }
.timeline-stop { position:relative; padding:0 0 16px 2px; }
.timeline-stop:before { content:''; position:absolute; left:-25px; top:4px; width:10px; height:10px; border-radius:50%; background:#2563eb; border:2px solid #fff; box-shadow:0 0 0 2px #bfdbfe; }
.timeline-stop.last:before { background:#16a34a; box-shadow:0 0 0 2px #bbf7d0; }
.timeline-name { font-weight:700; color:#193858; font-size:13px; }
.timeline-time { color:#64748b; font-size:11px; margin-top:2px; }
.leg-box { background:#f7faff; border:1px solid #e3ebf6; border-radius:11px; padding:12px; margin:8px 0; }
.transfer-box { margin:8px 0 13px 8px; padding:9px 12px; border-left:3px solid #f59e0b; background:#fff8eb; border-radius:8px; color:#854d0e; font-size:12px; }
.coming-soon { display:inline-block; background:#fff7ed; color:#9a3412; border:1px solid #fed7aa; border-radius:20px; padding:4px 9px; font-size:10px; font-weight:750; }
.destini-footer { display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px; border-top:1px solid #e2e8f0; margin-top:25px; padding:18px 0; color:#64748b; font-size:11px; }
@media (max-width: 800px) { .destini-nav,.destini-tagline,.destini-hero-art { display:none; } .destini-hero { padding:25px 22px; } .block-container { padding-left:.75rem; padding-right:.75rem; } }
</style>
""", unsafe_allow_html=True)


# ============================================================
# BUS LOADING ANIMATION
# ============================================================

def show_bus_loading(placeholder):

    loading_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            background: transparent !important;
            overflow: hidden;
        }

        .animation-container {
            width: 100%;
            height: 210px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: transparent;
        }

        svg {
            width: 100%;
            height: 200px;
            overflow: visible;
        }
    </style>
    </head>

    <body>
    <div class="animation-container">

    <svg viewBox="0 0 600 200"
         xmlns="http://www.w3.org/2000/svg">

        <defs>
            <filter id="busShadow">
                <feDropShadow
                    dx="0" dy="3"
                    stdDeviation="3"
                    flood-color="#000000"
                    flood-opacity="0.5"/>
            </filter>
        </defs>

        <!-- Curved road -->
        <path
            d="M 55 150 C 180 35, 260 185, 370 95 S 490 75, 535 45"
            fill="none"
            stroke="#64748B"
            stroke-width="5"
            stroke-linecap="round"
            stroke-dasharray="10 12"
        />

        <!-- Starting point -->
        <circle
            cx="55"
            cy="150"
            r="13"
            fill="#22C55E"
            stroke="#FFFFFF"
            stroke-width="3"
        />

        <path
            d="M 51 144 L 62 150 L 51 156 Z"
            fill="#FFFFFF"
        />

        <!-- Destination pin -->
        <g transform="translate(535 45)">
            <path
                d="M 0 0 C -24 -28 -20 -52 0 -52
                   C 20 -52 24 -28 0 0 Z"
                fill="#EF4444"
                stroke="#FFFFFF"
                stroke-width="3"
            />
            <circle cx="0" cy="-34" r="7" fill="#FFFFFF"/>
        </g>

        <!-- Moving bus -->
        <g filter="url(#busShadow)">

            <g>
                <animateMotion
                    dur="6s"
                    repeatCount="indefinite"
                    rotate="auto"
                    path="M 55 150 C 180 35, 260 185, 370 95 S 490 75, 525 52"
                />

                <!-- Bus body -->
                <rect
                    x="-30" y="-19"
                    width="60" height="34"
                    rx="7"
                    fill="#EF4444"
                    stroke="#111827"
                    stroke-width="3"
                />

                <!-- Front section -->
                <rect
                    x="17" y="-14"
                    width="10" height="19"
                    rx="3"
                    fill="#FACC15"
                />

                <!-- Windows -->
                <rect x="-23" y="-13" width="12" height="12"
                      rx="2" fill="#BAE6FD"/>

                <rect x="-8" y="-13" width="12" height="12"
                      rx="2" fill="#BAE6FD"/>

                <rect x="7" y="-13" width="9" height="12"
                      rx="2" fill="#BAE6FD"/>

                <!-- Lower yellow stripe -->
                <rect
                    x="-25" y="5"
                    width="50" height="6"
                    rx="2"
                    fill="#FACC15"
                />

                <!-- Wheels -->
                <circle cx="-17" cy="16" r="6"
                        fill="#111827"
                        stroke="#CBD5E1"
                        stroke-width="2"/>

                <circle cx="17" cy="16" r="6"
                        fill="#111827"
                        stroke="#CBD5E1"
                        stroke-width="2"/>
            </g>
        </g>

    </svg>
    </div>
    </body>
    </html>
    """

    with placeholder:
        st.components.v1.html(
            loading_html,
            height=215,
            scrolling=False
        )


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data(show_spinner=False)
def load_stops():

    stops = pd.read_csv(
        STOPS_FILE,
        dtype={"stop_id": str}
    )

    stops = stops.dropna(
        subset=["stop_id", "stop_name", "stop_lat", "stop_lon"]
    )

    stops = stops.drop_duplicates(
        subset=["stop_id"]
    )

    stops["display"] = (
        stops["stop_name"].astype(str)
        + " (ID: "
        + stops["stop_id"].astype(str)
        + ")"
    )

    return stops


@st.cache_data(show_spinner=False)
def load_journey_data():

    required_columns = [
        "trip_id",
        "from_stop",
        "to_stop",
        "departure_time",
        "arrival_time",
        "departure_seconds",
        "arrival_seconds",
        "stop_sequence",
        "route_short_name",
        "from_stop_name",
        "to_stop_name",
        "travel_time_seconds"
    ]

    df = pd.read_csv(
        CONNECTIONS_FILE,
        usecols=required_columns,
        dtype={
            "from_stop": str,
            "to_stop": str
        }
    )

    gps = pd.read_csv(
        GPS_FILE,
        dtype={
            "from_stop": str,
            "to_stop": str
        }
    )

    gps_lookup = {
        (str(row["from_stop"]), str(row["to_stop"])):
        float(row["estimated_minutes"])
        for _, row in gps.iterrows()
    }

    return df, gps_lookup


@st.cache_data(show_spinner=False)
def load_map_data():

    map_stops = pd.read_csv(
        STOPS_FILE,
        dtype={"stop_id": str}
    )

    map_stops = map_stops.dropna(
        subset=["stop_lat", "stop_lon"]
    )

    map_shapes = pd.read_csv(SHAPES_FILE)

    map_trips = pd.read_csv(
        TRIPS_FILE,
        dtype={"trip_id": str}
    )

    return map_stops, map_shapes, map_trips


@st.cache_resource(show_spinner=False)
def load_raptor():

    return load_raptor_data()


# ============================================================
# DIRECT JOURNEY ENGINE
# ============================================================

def find_direct_journeys(
    df,
    gps_lookup,
    origin_id,
    destination_id,
    departure_time
):

    departure_seconds = (
        departure_time.hour * 3600
        + departure_time.minute * 60
    )

    origin_edges = df[
        (df["from_stop"] == origin_id)
        & (df["departure_seconds"] >= departure_seconds)
    ]

    destination_edges = df[
        df["to_stop"] == destination_id
    ]

    direct = origin_edges.merge(
        destination_edges,
        on="trip_id",
        suffixes=("_start", "_end")
    )

    direct = direct[
        (direct["stop_sequence_end"] >= direct["stop_sequence_start"])
        & (direct["arrival_seconds_end"] >= direct["departure_seconds_start"])
    ]

    direct = direct.sort_values("arrival_seconds_end")

    results = []

    for _, row in direct.head(5).iterrows():

        scheduled = (
            row["arrival_seconds_end"]
            - row["departure_seconds_start"]
        ) / 60

        route = str(row["route_short_name_start"]).strip()

        estimated = scheduled
        used_gps = False

        if route == "764DOWN":

            if row["stop_sequence_start"] == row["stop_sequence_end"]:

                segments = df[
                    (df["trip_id"] == row["trip_id"])
                    & (df["stop_sequence"] == row["stop_sequence_start"])
                ]

            else:

                segments = df[
                    (df["trip_id"] == row["trip_id"])
                    & (df["stop_sequence"] >= row["stop_sequence_start"])
                    & (df["stop_sequence"] < row["stop_sequence_end"])
                ]

            segments = segments.sort_values("stop_sequence")
            estimated = 0

            for _, segment in segments.iterrows():

                pair = (
                    str(segment["from_stop"]),
                    str(segment["to_stop"])
                )

                if pair in gps_lookup:
                    estimated += gps_lookup[pair]
                    used_gps = True
                else:
                    estimated += segment["travel_time_seconds"] / 60

        estimated_arrival = (
            row["departure_seconds_start"] + estimated * 60
        ) % 86400

        arrival_hour = int(estimated_arrival // 3600)
        arrival_minute = int((estimated_arrival % 3600) // 60)

        results.append({
            "route": route,
            "trip": str(row["trip_id"]),
            "departure": row["departure_time_start"],
            "scheduled_arrival": row["arrival_time_end"],
            "estimated_arrival": f"{arrival_hour:02d}:{arrival_minute:02d}",
            "scheduled_duration": round(scheduled, 2),
            "estimated_duration": round(estimated, 2),
            "source": "GPS + Schedule" if used_gps else "Schedule only"
        })

    return results


# ============================================================
# MAP HELPERS
# ============================================================

def coordinate_distance(point_a, point_b):

    return math.sqrt(
        (point_a[0] - point_b[0]) ** 2
        + (point_a[1] - point_b[1]) ** 2
    )


def nearest_shape_index(coordinates, target):

    distances = [
        coordinate_distance(point, target)
        for point in coordinates
    ]

    return distances.index(min(distances))


def add_location_marker(
    map_object,
    coordinates,
    label,
    marker_type
):

    if marker_type == "start":
        color = "#22C55E"
        symbol = "▶"
        title = "START"

    elif marker_type == "end":
        color = "#EF4444"
        symbol = "⚑"
        title = "DESTINATION"

    else:
        color = "#F59E0B"
        symbol = "↔"
        title = "TRANSFER"

    marker_html = f"""
    <div style="
        width: 34px;
        height: 34px;
        background: {color};
        border: 3px solid white;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        box-shadow: 0 3px 9px rgba(0,0,0,0.55);
        display: flex;
        align-items: center;
        justify-content: center;
    ">
        <div style="
            transform: rotate(45deg);
            color: white;
            font-size: 15px;
            font-weight: bold;
        ">
            {symbol}
        </div>
    </div>
    """

    icon = folium.DivIcon(
        html=marker_html,
        icon_size=(34, 34),
        icon_anchor=(17, 34)
    )

    folium.Marker(
        location=coordinates,
        tooltip=title + ": " + label,
        popup=title + ": " + label,
        icon=icon,
        z_index_offset=1000
    ).add_to(map_object)


# ============================================================
# MAP CREATION
# ============================================================

def _matching_trip_for_leg(connections, stop_table, leg):
    """Find a GTFS trip matching a transfer leg's route and endpoint stops."""
    route = str(leg.get("route", "")).strip()
    from_name = str(leg.get("from_name", "")).strip().lower()
    to_name = str(leg.get("to_name", "")).strip().lower()

    starts = stop_table[
        stop_table["stop_name"].astype(str).str.strip().str.lower() == from_name
    ]["stop_id"].astype(str).tolist()
    ends = stop_table[
        stop_table["stop_name"].astype(str).str.strip().str.lower() == to_name
    ]["stop_id"].astype(str).tolist()
    if not starts or not ends:
        return None

    candidates = connections[
        connections["route_short_name"].astype(str).str.strip() == route
    ]
    if candidates.empty:
        return None

    starts_set, ends_set = set(starts), set(ends)
    for trip_id, trip_rows in candidates.groupby("trip_id", sort=False):
        trip_rows = trip_rows.sort_values("stop_sequence")
        start_rows = trip_rows[trip_rows["from_stop"].astype(str).isin(starts_set)]
        end_rows = trip_rows[trip_rows["to_stop"].astype(str).isin(ends_set)]
        if start_rows.empty or end_rows.empty:
            continue
        first_sequence = start_rows["stop_sequence"].min()
        last_sequence = end_rows.loc[
            end_rows["stop_sequence"] >= first_sequence, "stop_sequence"
        ]
        if not last_sequence.empty:
            return str(trip_id)
    return None


def _draw_trip_shape(map_object, trips, shapes, trip_id, start_coords=None,
                     end_coords=None, color="#2563eb", tooltip="Bus route"):
    trip_row = trips[trips["trip_id"].astype(str).str.strip() == str(trip_id).strip()]
    if trip_row.empty:
        return []
    shape_id = str(trip_row.iloc[0].get("shape_id", "")).strip()
    if not shape_id or shape_id.lower() == "nan":
        return []
    route_shape = shapes[shapes["shape_id"].astype(str).str.strip() == shape_id]
    if route_shape.empty:
        return []
    route_shape = route_shape.sort_values("shape_pt_sequence")
    coords = route_shape[["shape_pt_lat", "shape_pt_lon"]].dropna().astype(float).values.tolist()
    if len(coords) < 2:
        return []
    if start_coords is not None and end_coords is not None:
        a = nearest_shape_index(coords, start_coords)
        b = nearest_shape_index(coords, end_coords)
        coords = coords[a:b + 1] if a <= b else list(reversed(coords[b:a + 1]))
    if len(coords) >= 2:
        folium.PolyLine(coords, color=color, weight=7, opacity=0.92,
                        tooltip=tooltip).add_to(map_object)
    return coords


def create_journey_map(
    map_stops,
    map_shapes,
    map_trips,
    origin_id=None,
    destination_id=None,
    selected_trip=None,
    transfer_name=None,
    selected_legs=None,
    connections=None
):

    m = folium.Map(
        location=[28.6139, 77.2090],
        zoom_start=11,
        tiles="OpenStreetMap",
        control_scale=True
    )

    stops = map_stops.copy()
    trips = map_trips.copy()
    shapes = map_shapes.copy()

    stops["stop_id"] = stops["stop_id"].astype(str).str.strip()
    trips["trip_id"] = trips["trip_id"].astype(str).str.strip()
    trips["shape_id"] = trips["shape_id"].astype(str).str.strip()
    shapes["shape_id"] = shapes["shape_id"].astype(str).str.strip()

    bounds = []

    # Origin
    origin = (
        stops[stops["stop_id"] == str(origin_id).strip()]
        if origin_id is not None else pd.DataFrame()
    )

    origin_coords = None

    if not origin.empty:

        row = origin.iloc[0]

        origin_coords = [
            float(row["stop_lat"]),
            float(row["stop_lon"])
        ]

        add_location_marker(
            m, origin_coords, str(row["stop_name"]), "start"
        )

        bounds.append(origin_coords)

    # Destination
    destination = (
        stops[stops["stop_id"] == str(destination_id).strip()]
        if destination_id is not None else pd.DataFrame()
    )

    destination_coords = None

    if not destination.empty:

        row = destination.iloc[0]

        destination_coords = [
            float(row["stop_lat"]),
            float(row["stop_lon"])
        ]

        add_location_marker(
            m, destination_coords, str(row["stop_name"]), "end"
        )

        bounds.append(destination_coords)

    # Selected bus route
    if selected_trip is not None:

        trip_row = trips[
            trips["trip_id"] == str(selected_trip).strip()
        ]

        if not trip_row.empty:

            shape_id = trip_row.iloc[0]["shape_id"]

            if pd.notna(shape_id) and shape_id.lower() != "nan":

                route_shape = shapes[
                    shapes["shape_id"] == shape_id
                ].copy()

                for column in [
                    "shape_pt_sequence",
                    "shape_pt_lat",
                    "shape_pt_lon"
                ]:
                    route_shape[column] = pd.to_numeric(
                        route_shape[column],
                        errors="coerce"
                    )

                route_shape = route_shape.dropna(
                    subset=[
                        "shape_pt_sequence",
                        "shape_pt_lat",
                        "shape_pt_lon"
                    ]
                )

                route_shape = route_shape.sort_values(
                    "shape_pt_sequence"
                )

                if not route_shape.empty:

                    all_coordinates = [
                        [float(row["shape_pt_lat"]), float(row["shape_pt_lon"])]
                        for _, row in route_shape.iterrows()
                    ]

                    route_coordinates = all_coordinates

                    if (
                        origin_coords is not None
                        and destination_coords is not None
                        and len(all_coordinates) >= 2
                    ):

                        start_index = nearest_shape_index(
                            all_coordinates, origin_coords
                        )

                        end_index = nearest_shape_index(
                            all_coordinates, destination_coords
                        )

                        if start_index <= end_index:
                            route_coordinates = all_coordinates[
                                start_index:end_index + 1
                            ]
                        else:
                            route_coordinates = list(
                                reversed(
                                    all_coordinates[end_index:start_index + 1]
                                )
                            )

                    if len(route_coordinates) >= 2:

                        route_line = folium.PolyLine(
                            route_coordinates,
                            color="#3B82F6",
                            weight=7,
                            opacity=0.95,
                            tooltip="Selected bus journey"
                        ).add_to(m)

                        PolyLineTextPath(
                            route_line,
                            "  ➤  ",
                            repeat=True,
                            offset=7,
                            attributes={
                                "fill": "#FFFFFF",
                                "font-weight": "bold",
                                "font-size": "17"
                            }
                        ).add_to(m)

                        bounds.extend(route_coordinates)

                else:
                    st.warning("No route coordinates found for this trip.")

            else:
                st.warning("The selected trip has no valid GTFS shape ID.")

        else:
            st.warning(f"Trip {selected_trip} was not found in GTFS trips.txt.")

    # Draw both bus legs for a selected transfer journey.
    if selected_legs and connections is not None:
        leg_colors = ["#2563eb", "#f59e0b"]
        for leg_index, leg in enumerate(selected_legs):
            trip_id = _matching_trip_for_leg(connections, stops, leg)
            if not trip_id:
                continue
            start_matches = stops[
                stops["stop_name"].astype(str).str.strip().str.lower()
                == str(leg.get("from_name", "")).strip().lower()
            ]
            end_matches = stops[
                stops["stop_name"].astype(str).str.strip().str.lower()
                == str(leg.get("to_name", "")).strip().lower()
            ]
            start_coords = None if start_matches.empty else [
                float(start_matches.iloc[0]["stop_lat"]),
                float(start_matches.iloc[0]["stop_lon"])
            ]
            end_coords = None if end_matches.empty else [
                float(end_matches.iloc[0]["stop_lat"]),
                float(end_matches.iloc[0]["stop_lon"])
            ]
            coords = _draw_trip_shape(
                m, trips, shapes, trip_id, start_coords, end_coords,
                color=leg_colors[leg_index % len(leg_colors)],
                tooltip=f"Leg {leg_index + 1} · Route {leg.get('route', '')}"
            )
            bounds.extend(coords)

    # Transfer point
    if transfer_name:

        transfer = stops[
            stops["stop_name"].astype(str).str.strip().str.lower()
            == str(transfer_name).strip().lower()
        ]

        if not transfer.empty:

            row = transfer.iloc[0]

            transfer_coords = [
                float(row["stop_lat"]),
                float(row["stop_lon"])
            ]

            add_location_marker(
                m, transfer_coords, str(transfer_name), "transfer"
            )

            bounds.append(transfer_coords)

    # Map bounds
    if len(bounds) >= 2:
        m.fit_bounds(bounds, padding=(45, 45))

    elif len(bounds) == 1:
        m.location = bounds[0]
        m.zoom_start = 14

    return m


# ============================================================
# DIRECT JOURNEY RESULTS
# ============================================================

def _format_clock(value):
    """Format a GTFS time value without assuming it is a datetime."""
    if pd.isna(value):
        return "—"
    return str(value)[:5]


def _direct_timeline_rows(df, result, origin_id, destination_id):
    """Return the GTFS stop sequence between the selected boarding/alighting stops."""
    trip_rows = df[df["trip_id"].astype(str) == str(result["trip"])].copy()
    if trip_rows.empty:
        return []
    trip_rows["stop_sequence"] = pd.to_numeric(trip_rows["stop_sequence"], errors="coerce")
    trip_rows = trip_rows.dropna(subset=["stop_sequence"]).sort_values("stop_sequence")
    start_rows = trip_rows[trip_rows["from_stop"].astype(str) == str(origin_id)]
    end_rows = trip_rows[trip_rows["to_stop"].astype(str) == str(destination_id)]
    if start_rows.empty or end_rows.empty:
        return []
    start_seq = start_rows.iloc[0]["stop_sequence"]
    end_seq = end_rows[end_rows["stop_sequence"] >= start_seq].iloc[0]["stop_sequence"] if (end_rows["stop_sequence"] >= start_seq).any() else None
    if end_seq is None:
        return []
    segment = trip_rows[(trip_rows["stop_sequence"] >= start_seq) & (trip_rows["stop_sequence"] <= end_seq)]
    if segment.empty:
        return []
    timeline = []
    for _, row in segment.iterrows():
        timeline.append({"name": str(row["from_stop_name"]), "time": _format_clock(row["departure_time"]), "kind": "stop"})
    final_row = segment.iloc[-1]
    timeline.append({"name": str(final_row["to_stop_name"]), "time": _format_clock(final_row["arrival_time"]), "kind": "last"})
    # Avoid duplicate consecutive stop names in unusual feed records.
    cleaned = []
    for item in timeline:
        if not cleaned or item["name"] != cleaned[-1]["name"]:
            cleaned.append(item)
        else:
            cleaned[-1] = item
    return cleaned


def _render_timeline(items):
    if not items:
        st.caption("Stop-by-stop timetable details are unavailable for this option.")
        return
    html = '<div class="timeline">'
    for index, item in enumerate(items):
        last = " last" if index == len(items) - 1 else ""
        html += (
            f'<div class="timeline-stop{last}">'
            f'<div class="timeline-name">{item["name"]}</div>'
            f'<div class="timeline-time">{item["time"]}</div>'
            '</div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def show_direct_results(results):
    st.markdown('<div class="section-heading">Available direct routes</div>', unsafe_allow_html=True)
    if not results:
        st.info("No direct journeys found for this time. Try another departure time or check one-transfer options.")
        return None
    st.caption(f"{len(results)} route options · Historical GPS estimates where available")
    labels = [
        f"🚌  Route {r['route']}   ·   {r['departure']} → {r['estimated_arrival']}   ·   {r['estimated_duration']} min   ·   {r['source']}"
        for r in results
    ]
    selected = st.radio("Choose a direct bus", options=range(len(results)), format_func=lambda i: labels[i],
                        key="direct_selection", label_visibility="collapsed")
    return results[selected]


def show_transfer_results(results):
    st.markdown('<div class="section-heading">One-transfer journeys</div>', unsafe_allow_html=True)
    if not results:
        st.info("No one-transfer journeys found for this search.")
        return None
    st.caption(f"{len(results)} transfer option(s) · Both bus legs are included")
    labels = []
    for i, journey in enumerate(results):
        route_names = " → ".join(str(leg["route"]) for leg in journey["legs"])
        labels.append(f"⇄  Routes {route_names}   ·   {journey['total_minutes']:.1f} min   ·   1 transfer")
    selected = st.radio("Choose a transfer journey", options=range(len(results)), format_func=lambda i: labels[i],
                        key="transfer_selection", label_visibility="collapsed")
    return results[selected]


def render_direct_summary(result, df, origin_id, destination_id):
    st.markdown('<div class="section-heading">Your route, at a glance</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(f'<span class="route-pill">DIRECT BUS</span> &nbsp; <span class="route-card-title">Route {result["route"]}</span>', unsafe_allow_html=True)
        st.caption(f"Trip {result['trip']} · {result['source']}")
        a, b, c = st.columns(3)
        a.metric("Departure", str(result["departure"]))
        b.metric("Est. arrival", str(result["estimated_arrival"]))
        c.metric("Travel time", f"{result['estimated_duration']} min")
        st.markdown("**JOURNEY TIMELINE**")
        _render_timeline(_direct_timeline_rows(df, result, origin_id, destination_id))
        st.markdown("---")
        st.caption(f"Scheduled duration: {result['scheduled_duration']} min")
        st.caption("Historical GPS-informed estimate with schedule fallback." if result["source"] == "GPS + Schedule" else "Schedule-based estimate. Live bus location is not available.")


def render_transfer_summary(journey):
    st.markdown('<div class="section-heading">Your route, at a glance</div>', unsafe_allow_html=True)
    with st.container(border=True):
        route_names = " → ".join(str(leg["route"]) for leg in journey["legs"])
        st.markdown(f'<span class="route-pill">1 TRANSFER</span> &nbsp; <span class="route-card-title">Routes {route_names}</span>', unsafe_allow_html=True)
        st.metric("Total journey time", f"{journey['total_minutes']:.1f} min")
        st.markdown("**JOURNEY TIMELINE**")
        for i, leg in enumerate(journey["legs"]):
            st.markdown(f'<div class="leg-box"><b>🚌 Leg {i + 1} · Route {leg["route"]}</b><br><span style="color:#64748b;font-size:11px">{leg["departure"]} departure</span><br><b>{leg["from_name"]}</b><br><span style="color:#64748b;font-size:11px">↓ Get off · {leg["arrival"]}</span><br><b>{leg["to_name"]}</b></div>', unsafe_allow_html=True)
            if i == 0:
                st.markdown(f'<div class="transfer-box">↪ Change buses here · {leg["to_name"]}</div>', unsafe_allow_html=True)
        st.caption("Transfer timings are schedule-based. Historical GPS adjustment is not applied to these legs.")


# ============================================================
# DESTINI HEADER + FIGMA-MATCHED LANDING PAGE
# ============================================================

st.markdown("""
<div class="destini-topbar">
  <div class="destini-logo"><span class="destini-logo-mark"><img src="data:image/png;base64,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" alt="Delhi transport symbol"></span><span>DESTINI<span style="color:#2563eb">.</span></span></div>
  <div class="destini-nav"><span class="active">Find a route</span><span>How it works</span><span>About DESTINI</span></div>
  <div class="destini-tagline">● &nbsp; Made for your everyday journey</div>
</div>
<section class="destini-hero">
  <div class="destini-brand">DESTINI / DELHI TRANSIT</div>
  <h1 class="destini-title">Every journey starts<br>with a better route.</h1>
  <div class="destini-subtitle">Less searching. More moving. Discover Delhi bus routes, compare direct and transfer options, and plan your next journey with confidence.</div>
  <div class="destini-tags">
    <span class="destini-tag">✦ Smarter routes</span>
    <span class="destini-tag">✓ Historical GPS-informed estimates</span>
    <span class="destini-tag">⇄ Direct &amp; transfer journeys</span>
    <span class="destini-tag">Live tracking · Coming soon</span>
  </div>
  <svg class="destini-hero-art" viewBox="0 0 430 220" fill="none" aria-hidden="true"><path d="M0 170h150c70 0 30-105 100-105h180M70 220v-70c0-50 110-20 110-85V0" stroke="white" stroke-opacity=".12" stroke-width="24"/><path d="M0 170h150c70 0 30-105 100-105h180" stroke="white" stroke-opacity=".5" stroke-dasharray="6 9"/><circle cx="291" cy="65" r="17" fill="#80b5fa" fill-opacity=".25"/><circle cx="291" cy="65" r="7" fill="#bfdbfe"/><g transform="translate(116 102) rotate(-8)"><rect width="116" height="56" rx="12" fill="#e5efff"/><rect x="10" y="9" width="68" height="24" rx="4" fill="#3870a9"/><rect x="85" y="9" width="21" height="37" rx="4" fill="#3870a9"/><path d="M33 9v24M57 9v24" stroke="#e5efff" stroke-width="3"/><circle cx="24" cy="56" r="10" fill="#102747"/><circle cx="91" cy="56" r="10" fill="#102747"/><circle cx="24" cy="56" r="4" fill="#a4bcd9"/><circle cx="91" cy="56" r="4" fill="#a4bcd9"/></g></svg>
</section>
""", unsafe_allow_html=True)


# ============================================================
# MAIN APPLICATION
# ============================================================

try:
    # Only the small stop list is loaded on the landing page. Large files are
    # loaded after the user searches, then cached for later interactions.
    stops = load_stops()

    with st.container(border=True):
        st.markdown('<div class="section-heading">Where are you headed?</div>', unsafe_allow_html=True)
        with st.form("journey_search_form"):
            stop_options = stops["display"].tolist()
            f1, swap_col, f2, f3, submit_col = st.columns([1.15, 0.22, 1.15, 0.9, 0.85], vertical_alignment="bottom")
            with f1:
                origin_input = st.selectbox("From", stop_options, index=None, placeholder="Choose your starting stop")
            with swap_col:
                st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)
                st.markdown("<div style='text-align:center;color:#2563eb;font-size:20px'>⇄</div>", unsafe_allow_html=True)
            with f2:
                destination_input = st.selectbox("To", stop_options, index=None, placeholder="Choose your destination")
            with f3:
                departure_time = st.time_input("Departure time", value=time(8, 0))
            with submit_col:
                search = st.form_submit_button("⌕  Find routes", type="primary", use_container_width=True)
        st.caption("✓  A little planning goes a long way. Let’s find your best way there.")

    if search:
        if not origin_input or not destination_input:
            st.warning("Please select both bus stops.")
        elif origin_input == destination_input:
            st.warning("Please select two different stops.")
        else:
            origin_id = origin_input.split("(ID: ")[1].rstrip(")")
            destination_id = destination_input.split("(ID: ")[1].rstrip(")")
            start_seconds = departure_time.hour * 3600 + departure_time.minute * 60
            progress = st.empty()
            progress.info("Finding suitable bus journeys…")
            try:
                df, gps_lookup = load_journey_data()
                raptor_data = load_raptor()
                direct_results = find_direct_journeys(df, gps_lookup, origin_id, destination_id, departure_time)
                raptor_results = find_raptor_journeys(raptor_data, origin_id, destination_id, start_seconds,
                                                      max_transfers=1, transfer_buffer=300)
                transfer_results = [j for j in raptor_results if j["transfers"] == 1]
                st.session_state["journey_search"] = {
                    "origin_id": origin_id, "destination_id": destination_id,
                    "origin_name": origin_input, "destination_name": destination_input,
                    "departure_time": departure_time, "direct_results": direct_results,
                    "transfer_results": transfer_results
                }
                st.session_state.pop("direct_selection", None)
                st.session_state.pop("transfer_selection", None)
            finally:
                progress.empty()
            st.rerun()

    search_data = st.session_state.get("journey_search")
    if search_data:
        df, gps_lookup = load_journey_data()
        direct_results = search_data["direct_results"]
        transfer_results = search_data["transfer_results"]

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-heading'>{search_data['origin_name'].split(' (ID:')[0]} <span style='color:#94a3b8'>→</span> {search_data['destination_name'].split(' (ID:')[0]}</div>", unsafe_allow_html=True)
        st.caption(f"Departure at {search_data['departure_time'].strftime('%H:%M')} · Delhi bus journey options")

        all_durations = [r["estimated_duration"] for r in direct_results]
        stats = st.columns(3)
        stats[0].metric("Available direct routes", f"{len(direct_results):02d}", "Options for your journey")
        stats[1].metric("One-transfer options", f"{len(transfer_results):02d}", "Alternative connections")
        stats[2].metric("Fastest direct journey", f"{min(all_durations):.1f} min" if all_durations else "—", "GPS-informed where available")

        left, right = st.columns([1.65, 1], gap="large")
        selected_direct = None
        selected_transfer = None
        with left:
            direct_tab, transfer_tab = st.tabs([f"Direct routes ({len(direct_results)})", f"1 transfer ({len(transfer_results)})"])
            with direct_tab:
                selected_direct = show_direct_results(direct_results)
            with transfer_tab:
                selected_transfer = show_transfer_results(transfer_results)
        with right:
            if direct_results and transfer_results:
                detail_direct, detail_transfer = st.tabs(["Direct details", "Transfer details"])
                with detail_direct:
                    render_direct_summary(selected_direct or direct_results[0], df, search_data["origin_id"], search_data["destination_id"])
                with detail_transfer:
                    render_transfer_summary(selected_transfer or transfer_results[0])
            elif direct_results:
                render_direct_summary(selected_direct or direct_results[0], df, search_data["origin_id"], search_data["destination_id"])
            elif transfer_results:
                render_transfer_summary(selected_transfer or transfer_results[0])
            else:
                st.info("No journey options were found. Try a different departure time or nearby stops.")

        # Map stays available as a separate panel so the route cards and timeline
        # retain the same hierarchy as the Figma design.
        st.markdown("---")
        st.markdown('<div class="section-heading">Explore your route on the map</div>', unsafe_allow_html=True)
        map_choices = []
        if direct_results:
            map_choices.append("Direct bus")
        if transfer_results:
            map_choices.append("One-transfer journey")
        if map_choices:
            map_mode = st.radio("Map journey", map_choices, horizontal=True, label_visibility="collapsed", key="map_mode")
            map_stops, map_shapes, map_trips = load_map_data()
            selected_trip = None
            transfer_name = None
            selected_legs = None
            if map_mode == "Direct bus" and direct_results:
                active_direct = selected_direct or direct_results[0]
                selected_trip = active_direct["trip"]
            elif transfer_results:
                active_transfer = selected_transfer or transfer_results[0]
                selected_legs = active_transfer["legs"]
                transfer_name = active_transfer["legs"][0]["to_name"]
            journey_map = create_journey_map(
                map_stops, map_shapes, map_trips,
                origin_id=search_data["origin_id"], destination_id=search_data["destination_id"],
                selected_trip=selected_trip, transfer_name=transfer_name,
                selected_legs=selected_legs, connections=df
            )
            st_folium(journey_map, width=None, height=510, returned_objects=[],
                      key=f"figma_map_{search_data['origin_id']}_{search_data['destination_id']}_{map_mode}")
            st.caption("Static GTFS route shapes are shown. This is not live bus tracking.")
    else:
        st.markdown('<div class="destini-footer"><span>© DESTINI. Every journey matters.</span><span>Choose your departure and destination to discover available Delhi bus journeys.</span></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="destini-footer">
      <span>© DESTINI. Every journey matters.</span>
      <span>Delhi GTFS schedule data · Historical GPS-informed predictions · Live tracking <b style="color:#9a3412">Coming soon</b></span>
    </div>
    """, unsafe_allow_html=True)



except FileNotFoundError as error:

    st.error(f"Required project file not found: {error}")

except Exception as error:

    st.error(f"Something went wrong: {error}")
    st.exception(error)
