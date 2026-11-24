
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

INPUT = PROJECT / "data" / "processed" / "gps_travel_times_764.csv"
OUTPUT = PROJECT / "data" / "processed" / "gps_travel_time_lookup.csv"

df = pd.read_csv(INPUT)

lookup = (
    df.groupby(
        ["from_stop_id", "from_stop_name",
         "to_stop_id", "to_stop_name"],
        as_index=False
    )
    .agg(
        observations=("travel_seconds", "count"),
        median_seconds=("travel_seconds", "median"),
        mean_seconds=("travel_seconds", "mean"),
        min_seconds=("travel_seconds", "min"),
        max_seconds=("travel_seconds", "max")
    )
)

lookup["median_minutes"] = (
    lookup["median_seconds"] / 60
).round(2)

lookup = lookup.sort_values(
    ["observations", "median_seconds"],
    ascending=[False, True]
)

lookup.to_csv(OUTPUT, index=False)

print("\n========== GPS LOOKUP REPORT ==========")
print("Unique stop pairs:", len(lookup))
print("Total observations:", lookup["observations"].sum())

print("\nMost frequently observed stop pairs:")
print(lookup.head(20).to_string(index=False))

print("\nOutput:", OUTPUT)
