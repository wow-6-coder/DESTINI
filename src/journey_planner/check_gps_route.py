
import sqlite3
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

GPS_DB = (
    PROJECT / "data" / "historical_gps" /
    "sample" / "bus_movements_2026_10_01.db"
)

print("Connecting to GPS database...")

con = sqlite3.connect(str(GPS_DB))
cur = con.cursor()

print("Checking route ID 1000...")

cur.execute("""
    SELECT
        COUNT(*) AS records,
        COUNT(DISTINCT vehicle_id) AS vehicles,
        COUNT(DISTINCT trip_id) AS trips,
        MIN(timestamp),
        MAX(timestamp)
    FROM vehicle_feed
    WHERE route_id = 1000
""")

result = cur.fetchone()

print("\n========== GPS ROUTE REPORT ==========")
print("GPS records:", result[0])
print("Unique vehicles:", result[1])
print("Unique trips:", result[2])
print("First timestamp:", result[3])
print("Last timestamp:", result[4])

print("\nSample GPS trip IDs:")

cur.execute("""
    SELECT trip_id, COUNT(*) AS records
    FROM vehicle_feed
    WHERE route_id = 1000
      AND trip_id IS NOT NULL
      AND TRIM(trip_id) != ''
    GROUP BY trip_id
    ORDER BY records DESC
    LIMIT 15
""")

for row in cur.fetchall():
    print(row)

con.close()

print("=====================================")
