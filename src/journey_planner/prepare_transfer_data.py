
from pathlib import Path
import pandas as pd

PROJECT = Path(__file__).resolve().parents[2]
GTFS = PROJECT / "data" / "static_gtfs" / "extracted"
OUTPUT = PROJECT / "data" / "processed"

OUTPUT.mkdir(parents=True, exist_ok=True)


def to_seconds(value):
    h, m, s = map(int, value.split(":"))
    return h * 3600 + m * 60 + s


print("Reading GTFS stop times...")

stop_times = pd.read_csv(
    GTFS / "stop_times.txt",
    usecols=[
        "trip_id",
        "arrival_time",
        "departure_time",
        "stop_id",
        "stop_sequence"
    ],
    dtype={
        "trip_id": str,
        "stop_id": str,
        "stop_sequence": "int32"
    }
)

print("Converting times...")

stop_times["arrival_seconds"] = (
    stop_times["arrival_time"].map(to_seconds)
)

stop_times["departure_seconds"] = (
    stop_times["departure_time"].map(to_seconds)
)

print("Sorting records...")

stop_times = stop_times.sort_values(
    ["trip_id", "stop_sequence"]
)

print("Saving prepared data...")

stop_times.to_parquet(
    OUTPUT / "transfer_stop_times.parquet",
    index=False
)

print("Transfer data preparation completed!")
print("Total records:", len(stop_times))
print("Saved to:", OUTPUT / "transfer_stop_times.parquet")
