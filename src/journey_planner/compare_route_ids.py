import sqlite3
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

GPS_DB = (
    PROJECT / "data" / "historical_gps" /
    "sample" / "bus_movements_2026_10_01.db"
)

GTFS_ROUTES = (
    PROJECT / "data" / "static_gtfs" /
    "extracted" / "routes.txt"
)

print("Loading GTFS route IDs...")

routes = pd.read_csv(GTFS_ROUTES, dtype=str)

gtfs_ids = set(routes["route_id"].dropna())

print("GTFS unique route IDs:", len(gtfs_ids))

print("\nReading GPS route IDs...")

connection = sqlite3.connect(str(GPS_DB))

gps = pd.read_sql_query(
    """
    SELECT DISTINCT route_id
    FROM vehicle_feed
    WHERE route_id IS NOT NULL
    """,
    connection
)

connection.close()

def normalize(value):
    number = float(value)

    if number.is_integer():
        return str(int(number))

    return str(number)

gps_ids = set(gps["route_id"].apply(normalize))

print("GPS unique route IDs:", len(gps_ids))

matched = gps_ids.intersection(gtfs_ids)
gps_only = gps_ids - gtfs_ids
gtfs_only = gtfs_ids - gps_ids

print("\n========== ROUTE ID COMPARISON ==========")

print("Matching route IDs:", len(matched))
print("GPS-only route IDs:", len(gps_only))
print("GTFS-only route IDs:", len(gtfs_only))

print(
    "GPS route ID match percentage:",
    round(len(matched) / len(gps_ids) * 100, 2),
    "%"
)

print("\nSample matching IDs:")
print(sorted(matched)[:20])

print("\nSample GPS-only IDs:")
print(sorted(gps_only)[:20])

print("=========================================")