
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
FILE = PROJECT / "data" / "processed" / "gps_stop_matches_764.csv"

df = pd.read_csv(FILE)

print("TOTAL RECORDS:", len(df))
print("UNIQUE TRIPS:", df["trip_id"].nunique())

print("\n========== TIME CONSISTENCY ==========")

for trip_id in df["trip_id"].drop_duplicates().head(5):
    part = df[df["trip_id"] == trip_id].copy()

    print("\nTRIP:", trip_id)
    print("Records:", len(part))
    print("Unique timestamps:", part["timestamp"].nunique())
    print("Unique time values:", part["time"].nunique())
    print("First time:", part["time"].iloc[0])
    print("Last time:", part["time"].iloc[-1])

    print("\nFirst 8 observations:")
    print(
        part[["time", "timestamp", "nearest_stop_id",
              "speed", "distance_m"]]
        .head(8)
        .to_string(index=False)
    )

print("\n========== DUPLICATE CHECK ==========")
print("Duplicate timestamp rows:", df.duplicated(
    subset=["trip_id", "timestamp"]
).sum())

print("Duplicate time rows:", df.duplicated(
    subset=["trip_id", "time"]
).sum())
