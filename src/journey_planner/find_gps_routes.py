
import sqlite3
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

GPS_DB = PROJECT / "data" / "historical_gps" / "sample" / "bus_movements_2026_10_01.db"
GTFS_ROUTES = PROJECT / "data" / "static_gtfs" / "extracted" / "routes.txt"

con = sqlite3.connect(str(GPS_DB))

print("Finding routes with GPS observations...")

gps_routes = pd.read_sql_query("""
    SELECT
        CAST(route_id AS INTEGER) AS route_id,
        COUNT(*) AS gps_records,
        COUNT(DISTINCT vehicle_id) AS vehicles
    FROM vehicle_feed
    WHERE route_id IS NOT NULL
    GROUP BY route_id
    ORDER BY gps_records DESC
    LIMIT 30
""", con)

con.close()

routes = pd.read_csv(
    GTFS_ROUTES,
    dtype={"route_id": str}
)

gps_routes["route_id"] = gps_routes["route_id"].astype(str)

result = gps_routes.merge(
    routes[["route_id", "route_short_name", "route_long_name"]],
    on="route_id",
    how="left"
)

print("\n========== ROUTES WITH GPS DATA ==========")
print(result.to_string(index=False))
print("==========================================")
