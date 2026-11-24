
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

VISITS_FILE = PROJECT / "data" / "processed" / "gps_stop_visits_764_oct2.csv"
GTFS_DIR = PROJECT / "data" / "static_gtfs" / "extracted"

OUTPUT = PROJECT / "data" / "processed" / "gps_travel_times_764_oct2.csv"

print("Loading October 2 GPS stop visits...")

visits = pd.read_csv(VISITS_FILE)

print("Loading GTFS stop sequences...")

stop_times = pd.read_csv(
    GTFS_DIR / "stop_times.txt",
    dtype=str
)

trips = pd.read_csv(
    GTFS_DIR / "trips.txt",
    dtype=str
)

route_trips = set(
    trips.loc[trips["route_id"] == "2229", "trip_id"]
)

visits["trip_id"] = visits["trip_id"].astype(str)
visits["stop_id"] = visits["stop_id"].astype(str)

visits = visits[
    visits["trip_id"].isin(route_trips)
].copy()

stop_times["stop_sequence"] = pd.to_numeric(
    stop_times["stop_sequence"],
    errors="coerce"
)

visits = visits.merge(
    stop_times[["trip_id", "stop_id", "stop_sequence"]],
    on=["trip_id", "stop_id"],
    how="inner"
)

visits["first_seconds"] = (
    pd.to_timedelta(visits["first_time"]).dt.total_seconds()
)

visits["last_seconds"] = (
    pd.to_timedelta(visits["last_time"]).dt.total_seconds()
)

visits = visits.sort_values(
    ["trip_id", "first_seconds"]
)

visits["next_stop_id"] = visits.groupby("trip_id")["stop_id"].shift(-1)
visits["next_stop_name"] = visits.groupby("trip_id")["stop_name"].shift(-1)
visits["next_sequence"] = visits.groupby("trip_id")["stop_sequence"].shift(-1)
visits["next_first_seconds"] = visits.groupby("trip_id")["first_seconds"].shift(-1)

visits["sequence_gap"] = (
    visits["next_sequence"] - visits["stop_sequence"]
)

visits["travel_seconds"] = (
    visits["next_first_seconds"] - visits["last_seconds"]
)

valid = visits[
    (visits["sequence_gap"] == 1) &
    (visits["travel_seconds"] >= 30) &
    (visits["travel_seconds"] <= 900)
].copy()

segments = pd.DataFrame({
    "trip_id": valid["trip_id"],
    "from_stop_id": valid["stop_id"],
    "from_stop_name": valid["stop_name"],
    "to_stop_id": valid["next_stop_id"],
    "to_stop_name": valid["next_stop_name"],
    "from_sequence": valid["stop_sequence"],
    "to_sequence": valid["next_sequence"],
    "travel_seconds": valid["travel_seconds"]
})

segments["travel_minutes"] = (
    segments["travel_seconds"] / 60
)

segments.to_csv(OUTPUT, index=False)

print("\n========== OCTOBER 2 TRAVEL TIME REPORT ==========")
print("GPS stop visits with GTFS matches:", len(visits))
print("Valid consecutive-stop transitions:", len(segments))
print("Unique trips:", segments["trip_id"].nunique())
print("Unique stop pairs:", segments[
    ["from_stop_id", "to_stop_id"]
].drop_duplicates().shape[0])

if len(segments):
    print("Average travel time:", round(segments["travel_minutes"].mean(), 2), "minutes")
    print("Median travel time:", round(segments["travel_minutes"].median(), 2), "minutes")

print("Output:", OUTPUT)
print("=================================================")
