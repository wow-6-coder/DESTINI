
from pathlib import Path
from datetime import time
import pandas as pd
import streamlit as st

import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src" / "journey_planner"))

from raptor_engine import (
    load_raptor_data,
    find_raptor_journeys
)

# ---------------------------------
# PAGE CONFIGURATION
# ---------------------------------

st.set_page_config(
    page_title="Delhi Bus Journey Planner",
    page_icon="🚌",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

STOPS_FILE = DATA_DIR / "static_gtfs" / "extracted" / "stops.txt"
CONNECTIONS_FILE = DATA_DIR / "processed" / "bus_connections_enriched.csv"
GPS_FILE = DATA_DIR / "processed" / "route_764_integrated_estimates.csv"


# ---------------------------------
# LOAD DATA
# ---------------------------------

@st.cache_data
def load_stops():

    stops = pd.read_csv(
        STOPS_FILE,
        dtype={"stop_id": str}
    )

    stops = stops.dropna(subset=["stop_id", "stop_name"])
    stops = stops.drop_duplicates(subset=["stop_id"])

    stops["display"] = (
        stops["stop_name"].astype(str)
        + " (ID: "
        + stops["stop_id"]
        + ")"
    )

    return stops


@st.cache_data
def load_journey_data():

    required_columns = [
        "trip_id", "from_stop", "to_stop",
        "departure_time", "arrival_time",
        "departure_seconds", "arrival_seconds",
        "stop_sequence", "route_short_name",
        "from_stop_name", "to_stop_name",
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


# ---------------------------------
# DIRECT JOURNEY ENGINE
# ---------------------------------

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
        (df["from_stop"] == origin_id) &
        (df["departure_seconds"] >= departure_seconds)
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
        (direct["stop_sequence_end"] >= direct["stop_sequence_start"]) &
        (direct["arrival_seconds_end"] >=
         direct["departure_seconds_start"])
    ]

    direct = direct.sort_values("arrival_seconds_end")

    results = []

    for _, row in direct.head(5).iterrows():

        scheduled = (
            row["arrival_seconds_end"] -
            row["departure_seconds_start"]
        ) / 60

        route = str(row["route_short_name_start"]).strip()

        estimated = scheduled
        used_gps = False

        if route == "764DOWN":

            if row["stop_sequence_start"] == row["stop_sequence_end"]:

                segments = df[
                    (df["trip_id"] == row["trip_id"]) &
                    (df["stop_sequence"] == row["stop_sequence_start"])
                ]

            else:

                segments = df[
                    (df["trip_id"] == row["trip_id"]) &
                    (df["stop_sequence"] >= row["stop_sequence_start"]) &
                    (df["stop_sequence"] < row["stop_sequence_end"])
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
            "trip": row["trip_id"],
            "departure": row["departure_time_start"],
            "scheduled_arrival": row["arrival_time_end"],
            "estimated_arrival": f"{arrival_hour:02d}:{arrival_minute:02d}",
            "scheduled_duration": round(scheduled, 2),
            "estimated_duration": round(estimated, 2),
            "source": "GPS + Schedule" if used_gps else "Schedule only"
        })

    return results


# ---------------------------------
# DISPLAY DIRECT JOURNEYS
# ---------------------------------

def display_direct_journeys(results):

    st.subheader("🚌 Direct journeys")

    if not results:
        st.info("No direct journeys found.")
        return

    st.success(f"Found {len(results)} direct journey options.")

    for result in results:

        with st.container(border=True):

            st.subheader(f"Route {result['route']}")

            st.write(f"Trip ID: `{result['trip']}`")

            c1, c2, c3 = st.columns(3)

            c1.metric("Departure", result["departure"])
            c2.metric("Scheduled arrival", result["scheduled_arrival"])
            c3.metric("Estimated arrival", result["estimated_arrival"])

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
                st.success("Estimate source: GPS + Schedule")
            else:
                st.info("Estimate source: Schedule only")


# ---------------------------------
# DISPLAY TRANSFER JOURNEYS
# ---------------------------------


def display_transfer_journeys(results):

    print("DISPLAY FUNCTION RECEIVED:", len(results))

    st.subheader("One-transfer journeys")

    if not results:
        st.info(
            "No transfer required or available for this journey. "
            "Check the direct bus options above."
        )
        return

    st.success(f"Found {len(results)} one-transfer options.")

    for number, journey in enumerate(results, 1):

        with st.container(border=True):

            st.subheader(f"Journey option {number}")

            legs = journey["legs"]

            for i, leg in enumerate(legs):

                st.markdown(
                    f"**Bus {i + 1}: Route {leg['route']}**"
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"Board: {leg['from_name']}")
                    st.write(f"Departure: {leg['departure']}")

                with col2:
                    st.write(f"Alight: {leg['to_name']}")
                    st.write(f"Arrival: {leg['arrival']}")

                if i == 0:
                    st.info(
                        f"Transfer at: {leg['to_name']}"
                    )

            st.metric(
                "Total journey time",
                f"{journey['total_minutes']:.1f} minutes"
            )

            st.caption(
                "Based on scheduled GTFS departure and arrival times. "
                "GPS adjustment is not applied to transfer journeys."
            )

# ---------------------------------
# MAIN FRONTEND
# ---------------------------------

st.title("🚌 Delhi Bus Journey Planner")

st.write(
    "Find bus journeys using scheduled timings "
    "and historical GPS-informed estimates."
)

try:

    stops = load_stops()

    st.success(f"Loaded {len(stops):,} bus stops.")

    with st.spinner("Loading journey and GPS data..."):
        df, gps_lookup = load_journey_data()

    with st.spinner("Loading RAPTOR journey engine..."):
     raptor_data = load_raptor_data()

    st.subheader("Plan your journey")

    stop_options = stops["display"].tolist()

    col1, col2 = st.columns(2)

    with col1:
        origin = st.selectbox(
            "Starting bus stop",
            stop_options,
            index=None,
            placeholder="Search starting stop..."
        )

    with col2:
        destination = st.selectbox(
            "Destination bus stop",
            stop_options,
            index=None,
            placeholder="Search destination..."
        )

    departure_time = st.time_input(
        "Departure time",
        value=time(8, 0)
    )

    search = st.button(
        "🔍 Find buses",
        type="primary",
        use_container_width=True
    )

    if search:

        if not origin or not destination:
            st.warning("Please select both bus stops.")

        elif origin == destination:
            st.warning("Please select two different stops.")

        else:

            origin_id = origin.split("(ID: ")[1].rstrip(")")
            destination_id = destination.split("(ID: ")[1].rstrip(")")

            start_seconds = (
                departure_time.hour * 3600
                + departure_time.minute * 60
            )

            # DIRECT JOURNEYS
            with st.spinner("Finding direct journeys..."):

                direct_results = find_direct_journeys(
                    df,
                    gps_lookup,
                    origin_id,
                    destination_id,
                    departure_time
                )

            display_direct_journeys(direct_results)

            st.divider()

           # ONE-TRANSFER JOURNEYS

            with st.spinner("Searching for one-transfer journeys..."):

             raptor_results = find_raptor_journeys(
              raptor_data,
              origin_id,
              destination_id,
              start_seconds,
              max_transfers=1,
              transfer_buffer=300
                   )

            transfer_results = [
              journey for journey in raptor_results
               if journey["transfers"] == 1
                       ]

            display_transfer_journeys(transfer_results)

            print("\n===== FRONTEND TRANSFER DEBUG =====")
            print("RAPTOR returned:", len(raptor_results))
            print("Filtered transfers:", len(transfer_results))

        if raptor_results:
         print("First journey:", raptor_results[0])

        print("===================================\n")


except FileNotFoundError as e:

    st.error(f"Required data file not found: {e}")

except Exception as e:

    st.error(f"Something went wrong: {e}")
    st.exception(e)


