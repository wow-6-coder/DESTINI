import sqlite3
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

GPS_DB = (
    PROJECT / "data" / "historical_gps" /
    "sample" / "bus_movements_2026_10_01.db"
)

GTFS_TRIPS = (
    PROJECT / "data" / "static_gtfs" /
    "extracted" / "trips.txt"
)

print("Loading GTFS trip IDs...")

trips = pd.read_csv(GTFS_TRIPS, dtype=str)

gtfs_ids = set(trips["trip_id"].dropna().str.strip())

print("GTFS unique trip IDs:", len(gtfs_ids))

print("\nReading GPS trip IDs...")

connection = sqlite3.connect(str(GPS_DB))

gps = pd.read_sql_query(
    """
    SELECT DISTINCT trip_id
    FROM vehicle_feed
    WHERE trip_id IS NOT NULL
      AND TRIM(trip_id) != ''
    """,
    connection
)

connection.close()

gps_ids = set(gps["trip_id"].str.strip())

matched = gps_ids.intersection(gtfs_ids)
gps_only = gps_ids - gtfs_ids
gtfs_only = gtfs_ids - gps_ids

print("\n========== TRIP ID COMPARISON ==========")

print("GPS unique trip IDs:", len(gps_ids))
print("Matching trip IDs:", len(matched))
print("GPS-only trip IDs:", len(gps_only))
print("GTFS-only trip IDs:", len(gtfs_only))

if gps_ids:
    print(
        "GPS trip ID match percentage:",
        round(len(matched) / len(gps_ids) * 100, 2),
        "%"
    )

print("\nSample matching IDs:")
print(sorted(matched)[:20])

print("\nSample GPS-only IDs:")
print(sorted(gps_only)[:20])

print("========================================")