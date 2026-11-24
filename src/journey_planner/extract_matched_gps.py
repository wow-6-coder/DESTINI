
import sqlite3
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

GPS_DB = (
    PROJECT / "data" / "historical_gps" /
    "sample" / "bus_movements_2026_10_01.db"
)

GTFS_DIR = PROJECT / "data" / "static_gtfs" / "extracted"
OUTPUT = PROJECT / "data" / "processed" / "matched_gps_764.csv"

print("Loading GTFS trips for route 2229...")

trips = pd.read_csv(
    GTFS_DIR / "trips.txt",
    dtype=str
)

route_trips = set(
    trips.loc[trips["route_id"] == "2229", "trip_id"]
)

print("GTFS trips:", len(route_trips))

con = sqlite3.connect(str(GPS_DB))

# Find exact GPS trip IDs that match GTFS
placeholders = ",".join("?" for _ in route_trips)

query = f"""
SELECT vehicle_id, trip_id, lat, lng, speed, timestamp, time
FROM vehicle_feed
WHERE route_id = 2229
AND trip_id IN ({placeholders})
ORDER BY trip_id, timestamp
"""

print("Extracting matching GPS observations...")

gps = pd.read_sql_query(
    query,
    con,
    params=list(route_trips)
)

con.close()

gps.to_csv(OUTPUT, index=False)

print("\n========== EXTRACTION REPORT ==========")
print("Matching GPS records:", len(gps))
print("Matching GPS trips:", gps["trip_id"].nunique())
print("Vehicles:", gps["vehicle_id"].nunique())
print("Output:", OUTPUT)
print("=======================================")
