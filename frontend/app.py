
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
    page_title="Delhi Bus Navigator",
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
# DARK THEME
# ============================================================

st.markdown("""
<style>
.stApp {
    background: #080F1D !important;
    color: #F8FAFC !important;
}

header[data-testid="stHeader"] {
    background: #080F1D !important;
}

.block-container {
    max-width: 1650px;
    padding-top: 1.2rem;
    padding-bottom: 1rem;
}

.main-title {
    font-size: 32px;
    font-weight: 800;
    color: #F8FAFC !important;
}

.subtitle {
    color: #A8B5C8 !important;
    font-size: 14px;
    margin-top: 5px;
    margin-bottom: 22px;
}

.section-heading {
    font-size: 20px;
    font-weight: 750;
    color: #F8FAFC !important;
    margin-bottom: 12px;
}

[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stCaptionContainer"],
.stCaption,
.stRadio label,
.stRadio label p,
.stSelectbox label,
.stTimeInput label {
    color: #E2E8F0 !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: #111C30 !important;
    border: 1px solid #334155 !important;
    border-radius: 15px !important;
}

[data-testid="stMetric"] {
    background: #17243A !important;
    border: 1px solid #334155 !important;
    border-radius: 14px !important;
    padding: 13px !important;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p {
    color: #CBD5E1 !important;
}

[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div {
    color: #FFFFFF !important;
}

input, textarea {
    background: #17243A !important;
    color: #FFFFFF !important;
    border-color: #475569 !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

div[data-baseweb="select"] > div {
    background: #17243A !important;
    color: #FFFFFF !important;
    border-color: #475569 !important;
}

div[data-baseweb="select"] span {
    color: #FFFFFF !important;
}

div[data-baseweb="popover"],
div[data-baseweb="popover"] ul,
div[data-baseweb="popover"] li,
div[data-baseweb="menu"] {
    background: #17243A !important;
    color: #FFFFFF !important;
}

div[data-baseweb="menu"] * {
    color: #FFFFFF !important;
}

div[role="radiogroup"] label {
    background: #17243A !important;
    border: 1px solid #334155 !important;
    border-radius: 9px !important;
    padding: 9px 12px !important;
    margin-bottom: 6px !important;
}

div[role="radiogroup"] label p,
div[role="radiogroup"] label span,
div[role="radiogroup"] label div {
    color: #F8FAFC !important;
}

div.stButton > button,
div.stFormSubmitButton > button {
    background: #2563EB !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    min-height: 44px;
    font-weight: 700;
}

div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    background: #1D4ED8 !important;
    color: #FFFFFF !important;
}

[data-testid="stAlert"] {
    background: #17243A !important;
    border: 1px solid #475569 !important;
}

[data-testid="stAlert"] p,
[data-testid="stAlert"] span {
    color: #F8FAFC !important;
}

small,
.stCaption,
[data-testid="stCaptionContainer"] p {
    color: #A8B5C8 !important;
}

hr {
    border-color: #334155 !important;
}
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

@st.cache_data
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


@st.cache_data
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


@st.cache_data
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


@st.cache_resource
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

def create_journey_map(
    map_stops,
    map_shapes,
    map_trips,
    origin_id=None,
    destination_id=None,
    selected_trip=None,
    transfer_name=None
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

def show_direct_results(results):

    st.markdown(
        '<div class="section-heading">Direct buses</div>',
        unsafe_allow_html=True
    )

    if not results:
        st.info("No direct journeys found.")
        return None

    st.caption(f"{len(results)} direct journey option(s) found")

    labels = [
        (
            f"Route {result['route']} | "
            f"{result['departure']} → "
            f"{result['estimated_arrival']} | "
            f"{result['estimated_duration']} min"
        )
        for result in results
    ]

    selected = st.radio(
        "Select a direct journey to view it on the map",
        options=range(len(results)),
        format_func=lambda i: labels[i],
        key="direct_selection",
        label_visibility="collapsed"
    )

    for result in results:

        with st.container(border=True):

            st.markdown(f"### 🚌 Route {result['route']}")
            st.caption(f"Trip ID: {result['trip']}")

            c1, c2 = st.columns(2)

            c1.metric("Departure", str(result["departure"]))
            c2.metric("Estimated arrival", str(result["estimated_arrival"]))

            c1, c2 = st.columns(2)

            c1.metric(
                "Scheduled duration",
                f"{result['scheduled_duration']} min"
            )

            c2.metric(
                "Estimated duration",
                f"{result['estimated_duration']} min"
            )

            if result["source"] == "GPS + Schedule":
                st.success("GPS-informed estimate")
            else:
                st.info("Schedule-based estimate")

    return results[selected]


# ============================================================
# TRANSFER JOURNEY RESULTS
# ============================================================

def show_transfer_results(results):

    st.markdown(
        '<div class="section-heading">One-transfer journeys</div>',
        unsafe_allow_html=True
    )

    if not results:
        st.info("No one-transfer journeys found.")
        return None

    st.caption(f"{len(results)} transfer option(s) found")

    labels = []

    for i, journey in enumerate(results):

        route_names = " → ".join(
            str(leg["route"]) for leg in journey["legs"]
        )

        labels.append(
            f"Option {i + 1} | {route_names} | "
            f"{journey['total_minutes']:.1f} min"
        )

    selected = st.radio(
        "Select a transfer journey",
        options=range(len(results)),
        format_func=lambda i: labels[i],
        key="transfer_selection",
        label_visibility="collapsed"
    )

    journey = results[selected]

    with st.container(border=True):

        st.markdown(f"### Journey option {selected + 1}")

        for i, leg in enumerate(journey["legs"]):

            st.markdown(
                f"**🚌 Bus {i + 1}: Route {leg['route']}**"
            )

            c1, c2 = st.columns(2)

            c1.write(f"**Board**  \n{leg['from_name']}")
            c2.write(f"**Alight**  \n{leg['to_name']}")

            c1.write(f"Departure: {leg['departure']}")
            c2.write(f"Arrival: {leg['arrival']}")

            if i == 0:
                st.info(f"Transfer at {leg['to_name']}")

        st.metric(
            "Total journey time",
            f"{journey['total_minutes']:.1f} minutes"
        )

        st.caption(
            "Based on scheduled GTFS timings. "
            "GPS adjustment is not applied to transfer journeys."
        )

    return journey


# ============================================================
# APPLICATION HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🚌 Delhi Bus Navigator</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Plan your journey across Delhi using bus schedules '
    'and historical GPS-informed travel-time estimates.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# MAIN APPLICATION
# ============================================================

try:

    # --------------------------------------------------------
    # INITIAL DATA LOADING
    # --------------------------------------------------------

    loading_placeholder = st.empty()
    show_bus_loading(loading_placeholder)

    try:

        stops = load_stops()

        df, gps_lookup = load_journey_data()

        map_stops, map_shapes, map_trips = load_map_data()

        raptor_data = load_raptor()

    finally:

        loading_placeholder.empty()

    # --------------------------------------------------------
    # TWO-COLUMN LAYOUT
    # --------------------------------------------------------

    left_panel, right_panel = st.columns(
        [0.40, 0.60],
        gap="medium"
    )

    # ========================================================
    # LEFT PANEL
    # ========================================================

    with left_panel:

        with st.container(border=True):

            st.markdown(
                '<div class="section-heading">Plan your journey</div>',
                unsafe_allow_html=True
            )

            stop_options = stops["display"].tolist()

            with st.form("journey_search_form"):

                origin_input = st.selectbox(
                    "From",
                    stop_options,
                    index=None,
                    placeholder="Search starting bus stop..."
                )

                destination_input = st.selectbox(
                    "To",
                    stop_options,
                    index=None,
                    placeholder="Search destination..."
                )

                departure_time = st.time_input(
                    "Departure time",
                    value=time(8, 0)
                )

                search = st.form_submit_button(
                    "🔍 Find buses",
                    type="primary",
                    use_container_width=True
                )

            # Search action
            if search:

                if not origin_input or not destination_input:

                    st.warning("Please select both bus stops.")

                elif origin_input == destination_input:

                    st.warning("Please select two different stops.")

                else:

                    origin_id = origin_input.split("(ID: ")[1].rstrip(")")
                    destination_id = destination_input.split("(ID: ")[1].rstrip(")")

                    start_seconds = (
                        departure_time.hour * 3600
                        + departure_time.minute * 60
                    )

                    search_loading = st.empty()
                    show_bus_loading(search_loading)

                    try:

                        direct_results = find_direct_journeys(
                            df,
                            gps_lookup,
                            origin_id,
                            destination_id,
                            departure_time
                        )

                        raptor_results = find_raptor_journeys(
                            raptor_data,
                            origin_id,
                            destination_id,
                            start_seconds,
                            max_transfers=1,
                            transfer_buffer=300
                        )

                        transfer_results = [
                            journey
                            for journey in raptor_results
                            if journey["transfers"] == 1
                        ]

                        st.session_state["journey_search"] = {
                            "origin_id": origin_id,
                            "destination_id": destination_id,
                            "origin_name": origin_input,
                            "destination_name": destination_input,
                            "departure_time": departure_time,
                            "direct_results": direct_results,
                            "transfer_results": transfer_results
                        }

                        st.session_state.pop("direct_selection", None)
                        st.session_state.pop("transfer_selection", None)

                    finally:

                        search_loading.empty()

                    st.rerun()

        # ----------------------------------------------------
        # DISPLAY RESULTS
        # ----------------------------------------------------

        search_data = st.session_state.get("journey_search")

        selected_direct = None
        selected_transfer = None

        if search_data:

            st.markdown("---")

            st.caption(f"FROM: {search_data['origin_name']}")
            st.caption(f"TO: {search_data['destination_name']}")

            st.caption(
                "Departure: "
                + search_data["departure_time"].strftime("%H:%M")
            )

            selected_direct = show_direct_results(
                search_data["direct_results"]
            )

            st.markdown("---")

            selected_transfer = show_transfer_results(
                search_data["transfer_results"]
            )

        else:

            st.info(
                "Choose your starting point and destination "
                "to discover available bus journeys."
            )

    # ========================================================
    # RIGHT PANEL: MAP
    # ========================================================

    with right_panel:

        st.markdown(
            '<div class="section-heading">Delhi bus network</div>',
            unsafe_allow_html=True
        )

        search_data = st.session_state.get("journey_search")

        if search_data:

            transfer_name = None
            selected_trip = None

            if selected_direct:
                selected_trip = selected_direct["trip"]

            elif selected_transfer:
                transfer_name = selected_transfer["legs"][0]["to_name"]

            journey_map = create_journey_map(
                map_stops,
                map_shapes,
                map_trips,
                origin_id=search_data["origin_id"],
                destination_id=search_data["destination_id"],
                selected_trip=selected_trip,
                transfer_name=transfer_name
            )

            map_key = (
                f"journey_map_"
                f"{search_data['origin_id']}_"
                f"{search_data['destination_id']}_"
                f"{selected_trip or 'transfer'}_"
                f"{transfer_name or 'none'}"
            )

            st_folium(
                journey_map,
                width=None,
                height=680,
                returned_objects=[],
                key=map_key
            )

            if selected_direct:

                st.success(
                    f"Showing the selected journey for "
                    f"Route {selected_direct['route']}."
                )

            elif selected_transfer:

                st.info(
                    "Showing the starting point, destination "
                    "and transfer location. Individual bus-leg "
                    "route shapes are not drawn in this version."
                )

        else:

            network_map = folium.Map(
                location=[28.6139, 77.2090],
                zoom_start=11,
                tiles="OpenStreetMap",
                control_scale=True
            )

            st_folium(
                network_map,
                width=None,
                height=680,
                returned_objects=[],
                key="delhi_network_map"
            )

            st.caption(
                "Search for a journey to display its locations "
                "and selected bus route."
            )

    # ========================================================
    # FOOTER
    # ========================================================

    st.markdown("---")

    st.caption(
        "Delhi Bus Navigator | GTFS schedule data + "
        "historical GPS-informed predictions | "
        "Experimental journey-planning system"
    )


except FileNotFoundError as error:

    st.error(f"Required project file not found: {error}")

except Exception as error:

    st.error(f"Something went wrong: {error}")
    st.exception(error)

