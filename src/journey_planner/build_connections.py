
import pandas as pd
from pathlib import Path

# Project paths
PROJECT = Path(__file__).resolve().parents[2]
GTFS_DIR = PROJECT / "data" / "static_gtfs" / "extracted"
OUTPUT_DIR = PROJECT / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading GTFS stop times...")

stop_times = pd.read_csv(
    GTFS_DIR / "stop_times.txt",
    dtype={"trip_id": str, "stop_id": str}
)

print("Records loaded:", len(stop_times))

# Sort every trip by its stop sequence
stop_times = stop_times.sort_values(
    ["trip_id", "stop_sequence"]
).reset_index(drop=True)

# Get the next stop within the same trip
stop_times["next_stop_id"] = (
    stop_times.groupby("trip_id")["stop_id"].shift(-1)
)

stop_times["next_arrival_time"] = (
    stop_times.groupby("trip_id")["arrival_time"].shift(-1)
)

# Remove final stops that have no following stop
connections = stop_times.dropna(
    subset=["next_stop_id", "next_arrival_time"]
).copy()

# Keep useful columns
connections = connections[[
    "trip_id",
    "stop_id",
    "departure_time",
    "next_stop_id",
    "next_arrival_time",
    "stop_sequence"
]]

connections = connections.rename(columns={
    "stop_id": "from_stop",
    "departure_time": "departure_time",
    "next_stop_id": "to_stop",
    "next_arrival_time": "arrival_time"
})

# Calculate scheduled travel time in seconds
def time_to_seconds(value):
    h, m, s = map(int, value.split(":"))
    return h * 3600 + m * 60 + s

connections["departure_seconds"] = (
    connections["departure_time"].apply(time_to_seconds)
)

connections["arrival_seconds"] = (
    connections["arrival_time"].apply(time_to_seconds)
)

connections["travel_time_seconds"] = (
    connections["arrival_seconds"] -
    connections["departure_seconds"]
)

# Save connections
output_file = OUTPUT_DIR / "bus_connections.csv"
connections.to_csv(output_file, index=False)

print("\n========== CONNECTION BUILD COMPLETE ==========")
print("Total connections:", len(connections))
print("Unique trips:", connections["trip_id"].nunique())
print("Unique starting stops:", connections["from_stop"].nunique())
print("Unique ending stops:", connections["to_stop"].nunique())
print("Output:", output_file)
print("================================================")
