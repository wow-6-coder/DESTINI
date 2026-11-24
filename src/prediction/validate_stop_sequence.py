
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

VISITS_FILE = PROJECT / "data" / "processed" / "gps_stop_visits_764.csv"
GTFS_DIR = PROJECT / "data" / "static_gtfs" / "extracted"

visits = pd.read_csv(VISITS_FILE)
stop_times = pd.read_csv(
    GTFS_DIR / "stop_times.txt",
    dtype=str
)

# Keep only the GTFS fields needed
stop_times = stop_times[
    ["trip_id", "stop_id", "stop_sequence"]
].copy()

stop_times["stop_sequence"] = pd.to_numeric(
    stop_times["stop_sequence"],
    errors="coerce"
)

visits["stop_id"] = visits["stop_id"].astype(str)

# Match GPS stop visits to their official GTFS sequence
merged = visits.merge(
    stop_times,
    left_on=["trip_id", "stop_id"],
    right_on=["trip_id", "stop_id"],
    how="left"
)

matched = merged.dropna(subset=["stop_sequence"]).copy()

print("\n========== SEQUENCE VALIDATION ==========")
print("GPS stop visits:", len(visits))
print("Visits found in GTFS:", len(matched))
print(
    "GTFS match percentage:",
    round(len(matched) / len(visits) * 100, 2), "%"
)

print("\n========== SAMPLE TRIP VALIDATION ==========")

for trip_id in visits["trip_id"].drop_duplicates().head(5):
    sample = matched[matched["trip_id"] == trip_id].copy()
    sample = sample.sort_values("first_time")

    sequences = sample["stop_sequence"].tolist()

    increases = sum(
        sequences[i] > sequences[i - 1]
        for i in range(1, len(sequences))
    )

    decreases = sum(
        sequences[i] < sequences[i - 1]
        for i in range(1, len(sequences))
    )

    print("\nTrip:", trip_id)
    print("Matched visits:", len(sample))
    print("Forward transitions:", increases)
    print("Backward transitions:", decreases)

    print(
        sample[
            ["stop_name", "stop_sequence",
             "first_time", "last_time", "observations"]
        ].head(15).to_string(index=False)
    )

print("\n========== LONG STOP VISITS ==========")

visits["duration_minutes"] = (
    pd.to_timedelta(visits["last_time"]).dt.total_seconds()
    - pd.to_timedelta(visits["first_time"]).dt.total_seconds()
) / 60

print(
    visits[visits["duration_minutes"] > 5][
        ["trip_id", "stop_name", "duration_minutes", "observations"]
    ].head(15).to_string(index=False)
)
