
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

GPS_FILE = PROJECT / "data" / "processed" / "gps_travel_time_lookup.csv"
GTFS_FILE = PROJECT / "data" / "processed" / "bus_connections_enriched.csv"
OUTPUT_FILE = PROJECT / "data" / "processed" / "gps_vs_schedule_comparison.csv"


def clean_id(series):
    return (
        series.astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )


# Load data
gps = pd.read_csv(GPS_FILE)
gtfs = pd.read_csv(GTFS_FILE)

# Normalize stop IDs and route ID
for col in ["from_stop_id", "to_stop_id"]:
    gps[col] = clean_id(gps[col])

for col in ["from_stop", "to_stop", "route_id"]:
    gtfs[col] = clean_id(gtfs[col])

# Keep only route 764DOWN (route ID 2229)
gtfs = gtfs[gtfs["route_id"] == "2229"].copy()

# Calculate scheduled median for each consecutive stop pair
schedule = (
    gtfs.groupby(["from_stop", "to_stop"], as_index=False)
    .agg(
        scheduled_observations=("travel_time_seconds", "count"),
        scheduled_median_seconds=("travel_time_seconds", "median")
    )
)

# Match GPS and scheduled stop pairs
comparison = gps.merge(
    schedule,
    left_on=["from_stop_id", "to_stop_id"],
    right_on=["from_stop", "to_stop"],
    how="inner"
)

comparison["difference_seconds"] = (
    comparison["median_seconds"]
    - comparison["scheduled_median_seconds"]
)

comparison["difference_percent"] = (
    comparison["difference_seconds"]
    / comparison["scheduled_median_seconds"].replace(0, pd.NA)
    * 100
).round(1)

comparison["gps_median_minutes"] = (
    comparison["median_seconds"] / 60
).round(2)

comparison["scheduled_median_minutes"] = (
    comparison["scheduled_median_seconds"] / 60
).round(2)

comparison = comparison.sort_values(
    "observations", ascending=False
)

comparison.to_csv(OUTPUT_FILE, index=False)

print("\n========== GPS VS SCHEDULE REPORT ==========")
print("GPS stop pairs:", len(gps))
print("Scheduled stop pairs on route 2229:", len(schedule))
print("Successfully compared pairs:", len(comparison))

if len(comparison) > 0:
    print("\nOverall comparison:")
    print(
        "Average GPS median:",
        round(comparison["median_seconds"].mean(), 2),
        "seconds"
    )
    print(
        "Average scheduled median:",
        round(comparison["scheduled_median_seconds"].mean(), 2),
        "seconds"
    )
    print(
        "Pairs where GPS is slower:",
        (comparison["difference_seconds"] > 0).sum()
    )
    print(
        "Pairs where GPS is faster:",
        (comparison["difference_seconds"] < 0).sum()
    )

    print("\nTop 20 matched pairs:")
    columns = [
        "from_stop_name",
        "to_stop_name",
        "observations",
        "gps_median_minutes",
        "scheduled_median_minutes",
        "difference_percent"
    ]
    print(comparison[columns].head(20).to_string(index=False))
else:
    print("No matching stop pairs found. Check stop IDs and route ID.")

print("\nOutput:", OUTPUT_FILE)
