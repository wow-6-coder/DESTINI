
import sqlite3
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

GPS_DB = (
    PROJECT / "data" / "historical_gps" / "sample"
    / "bus_movements_2026_10_02.db"
)

GTFS_TRIPS = (
    PROJECT / "data" / "static_gtfs" / "extracted"
    / "trips.txt"
)

OUTPUT = (
    PROJECT / "data" / "processed"
    / "matched_gps_764_oct2.csv"
)

print("Loading GTFS trips...")

trips = pd.read_csv(GTFS_TRIPS, dtype=str)

route_trips = set(
    trips.loc[trips["route_id"] == "2229", "trip_id"]
)

print("GTFS route 2229 trips:", len(route_trips))

print("Extracting October 2 GPS observations...")

con = sqlite3.connect(str(GPS_DB))

query = """
SELECT
    vehicle_id,
    trip_id,
    lat,
    lng,
    speed,
    timestamp,
    time
FROM vehicle_feed
WHERE CAST(route_id AS INTEGER) = 2229
"""

gps = pd.read_sql_query(query, con)
con.close()

print("Total route GPS records:", len(gps))

gps["trip_id"] = gps["trip_id"].astype(str)

gps = gps[gps["trip_id"].isin(route_trips)].copy()

print("Records with matching GTFS trips:", len(gps))
print("Unique matched trips:", gps["trip_id"].nunique())

gps.to_csv(OUTPUT, index=False)

print("\n========== OCTOBER 2 EXTRACTION ==========")
print("Output:", OUTPUT)
print("Records:", len(gps))
print("Unique trips:", gps["trip_id"].nunique())
print("=========================================")
