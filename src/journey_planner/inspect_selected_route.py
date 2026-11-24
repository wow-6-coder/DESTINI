
import sqlite3
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

GPS_DB = (
    PROJECT / "data" / "historical_gps" /
    "sample" / "bus_movements_2026_10_01.db"
)

GTFS = PROJECT / "data" / "static_gtfs" / "extracted"

con = sqlite3.connect(str(GPS_DB))

print("Inspecting GPS route 2229...")

gps_trips = pd.read_sql_query("""
    SELECT
        trip_id,
        vehicle_id,
        COUNT(*) AS records,
        MIN(timestamp) AS first_timestamp,
        MAX(timestamp) AS last_timestamp
    FROM vehicle_feed
    WHERE route_id = 2229
      AND trip_id IS NOT NULL
      AND TRIM(trip_id) != ''
    GROUP BY trip_id, vehicle_id
    ORDER BY records DESC
    LIMIT 20
""", con)

print("\nTOP GPS TRIPS:")
print(gps_trips.to_string(index=False))

print("\nLoading matching GTFS trips...")

gtfs_trips = pd.read_csv(
    GTFS / "trips.txt",
    dtype=str
)

gtfs_route = gtfs_trips[
    gtfs_trips["route_id"] == "2229"
]

gps_ids = set(gps_trips["trip_id"].astype(str))
gtfs_ids = set(gtfs_route["trip_id"].astype(str))

print("\nGTFS trips for route:", len(gtfs_route))
print("Matching sample GPS trip IDs:", len(gps_ids & gtfs_ids))

print("\nSample matching IDs:")
print(sorted(gps_ids & gtfs_ids)[:10])

# Retrieve a few actual GPS observations
sample_trip = gps_trips.iloc[0]["trip_id"]

print("\nGPS observations for sample trip:", sample_trip)

sample = pd.read_sql_query("""
    SELECT vehicle_id, lat, lng, speed, timestamp, time
    FROM vehicle_feed
    WHERE route_id = 2229 AND trip_id = ?
    ORDER BY timestamp
    LIMIT 10
""", con, params=(sample_trip,))

print(sample.to_string(index=False))

con.close()

print("\nINSPECTION COMPLETE")
