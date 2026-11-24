import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT / "data" / "static_gtfs" / "extracted"
PROCESSED_DIR = PROJECT / "data" / "processed"

print("Loading cleaned connections...")

connections = pd.read_csv(
    PROCESSED_DIR / "bus_connections_clean.csv",
    dtype={"trip_id": str, "from_stop": str, "to_stop": str}
)

print("Loading GTFS tables...")

trips = pd.read_csv(
    DATA_DIR / "trips.txt",
    dtype={"trip_id": str, "route_id": str}
)

routes = pd.read_csv(
    DATA_DIR / "routes.txt",
    dtype={"route_id": str}
)

stops = pd.read_csv(
    DATA_DIR / "stops.txt",
    dtype={"stop_id": str}
)

# Add route information using trip_id
data = connections.merge(
    trips[["trip_id", "route_id", "service_id", "trip_headsign"]],
    on="trip_id",
    how="left"
)

# Add route names
data = data.merge(
    routes[["route_id", "route_short_name", "route_long_name"]],
    on="route_id",
    how="left"
)

# Add starting stop information
from_stops = stops[
    ["stop_id", "stop_name", "stop_lat", "stop_lon"]
].rename(columns={
    "stop_id": "from_stop",
    "stop_name": "from_stop_name",
    "stop_lat": "from_lat",
    "stop_lon": "from_lon"
})

data = data.merge(
    from_stops,
    on="from_stop",
    how="left"
)

# Add destination stop information
to_stops = stops[
    ["stop_id", "stop_name", "stop_lat", "stop_lon"]
].rename(columns={
    "stop_id": "to_stop",
    "stop_name": "to_stop_name",
    "stop_lat": "to_lat",
    "stop_lon": "to_lon"
})

data = data.merge(
    to_stops,
    on="to_stop",
    how="left"
)

output = PROCESSED_DIR / "bus_connections_enriched.csv"

data.to_csv(output, index=False)

print("\n========== ENRICHMENT COMPLETE ==========")
print("Total connections:", len(data))
print("Missing route IDs:", data["route_id"].isna().sum())
print("Missing starting stop names:", data["from_stop_name"].isna().sum())
print("Missing destination stop names:", data["to_stop_name"].isna().sum())
print("Missing starting coordinates:", data["from_lat"].isna().sum())
print("Missing destination coordinates:", data["to_lat"].isna().sum())
print("Output:", output)
print("=========================================")

print("\nSample enriched records:")
print(data[[
    "route_id",
    "route_short_name",
    "from_stop_name",
    "to_stop_name",
    "travel_time_seconds"
]].head(10).to_string(index=False))