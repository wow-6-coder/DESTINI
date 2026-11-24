
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

INPUT = PROJECT / "data" / "processed" / "gps_stop_matches_764_oct2.csv"
OUTPUT = PROJECT / "data" / "processed" / "gps_stop_visits_764_oct2.csv"

print("Loading October 2 GPS stop matches...")

df = pd.read_csv(INPUT)

df = df[
    (df["is_matched"] == True) &
    (df["distance_m"] <= 150)
].copy()

df["time_seconds"] = (
    pd.to_timedelta(df["time"]).dt.total_seconds()
)

df = df.sort_values(
    ["trip_id", "time_seconds"]
).reset_index(drop=True)

df["new_visit"] = (
    (df["trip_id"] != df["trip_id"].shift()) |
    (df["nearest_stop_id"] != df["nearest_stop_id"].shift())
)

df["visit_group"] = df["new_visit"].cumsum()

visits = (
    df.groupby(
        ["trip_id", "vehicle_id", "visit_group"],
        as_index=False
    )
    .agg(
        stop_id=("nearest_stop_id", "first"),
        stop_name=("nearest_stop_name", "first"),
        first_time=("time_seconds", "min"),
        last_time=("time_seconds", "max"),
        observations=("time", "count"),
        average_distance=("distance_m", "mean")
    )
)

visits = visits.sort_values(
    ["trip_id", "first_time"]
)

visits["first_time"] = pd.to_timedelta(
    visits["first_time"], unit="s"
).astype(str)

visits["last_time"] = pd.to_timedelta(
    visits["last_time"], unit="s"
).astype(str)

visits.to_csv(OUTPUT, index=False)

print("\n========== OCTOBER 2 STOP VISIT REPORT ==========")
print("Matched GPS observations:", len(df))
print("Extracted stop visits:", len(visits))
print("Unique trips:", visits["trip_id"].nunique())
print("Unique stops:", visits["stop_id"].nunique())
print("Output:", OUTPUT)

