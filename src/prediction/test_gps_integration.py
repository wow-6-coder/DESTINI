
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
DATA = PROJECT / "data" / "processed"

connections = pd.read_csv(
    DATA / "bus_connections_enriched.csv",
    dtype={"from_stop": str, "to_stop": str}
)

gps = pd.read_csv(
    DATA / "gps_adjusted_travel_times.csv",
    dtype={"from_stop_id": str, "to_stop_id": str}
)

# Keep only route 764DOWN connections
route = connections[
    connections["route_short_name"].astype(str).str.strip()
    == "764DOWN"
].copy()

# One scheduled median per adjacent stop pair
scheduled = (
    route.groupby(["from_stop", "to_stop"], as_index=False)
    ["travel_time_seconds"]
    .median()
)

scheduled["scheduled_minutes"] = (
    scheduled["travel_time_seconds"] / 60
)

# Join GPS estimates by exact stop IDs
comparison = scheduled.merge(
    gps[
        ["from_stop_id", "to_stop_id",
         "adjusted_minutes", "observations"]
    ],
    left_on=["from_stop", "to_stop"],
    right_on=["from_stop_id", "to_stop_id"],
    how="left"
)

comparison["estimated_minutes"] = (
    comparison["adjusted_minutes"]
    .fillna(comparison["scheduled_minutes"])
)

comparison["estimate_source"] = (
    comparison["adjusted_minutes"]
    .notna()
    .map({True: "GPS + Schedule", False: "Schedule only"})
)

comparison.to_csv(
    DATA / "route_764_integrated_estimates.csv",
    index=False
)

print("\n========== GPS INTEGRATION REPORT ==========")
print("Route:", "764DOWN")
print("Scheduled stop pairs:", len(comparison))
print(
    "Pairs using GPS:",
    comparison["adjusted_minutes"].notna().sum()
)
print(
    "Pairs using schedule fallback:",
    comparison["adjusted_minutes"].isna().sum()
)

print("\nSample estimates:")
print(
    comparison[
        [
            "from_stop",
            "to_stop",
            "scheduled_minutes",
            "adjusted_minutes",
            "estimated_minutes",
            "estimate_source"
        ]
    ].head(20).to_string(index=False)
)

print("\nOutput:", DATA / "route_764_integrated_estimates.csv")
