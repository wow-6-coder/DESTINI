import sqlite3
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

GPS_DIR = PROJECT / "data" / "historical_gps" / "sample"

db_files = list(GPS_DIR.glob("*.db"))

print("GPS databases found:", len(db_files))

if not db_files:
    print("No GPS database found yet.")
    raise SystemExit

db_path = db_files[0]

print("Inspecting:", db_path.name)

connection = sqlite3.connect(str(db_path))

cursor = connection.cursor()

cursor.execute("PRAGMA table_info(vehicle_feed)")
print("\nTable columns:")
for row in cursor.fetchall():
    print(row)

cursor.execute("SELECT COUNT(*) FROM vehicle_feed")
print("\nTotal GPS records:", cursor.fetchone()[0])

cursor.execute("""
    SELECT route_id, COUNT(*) AS records
    FROM vehicle_feed
    GROUP BY route_id
    ORDER BY records DESC
    LIMIT 20
""")

print("\nMost frequent GPS route IDs:")
for row in cursor.fetchall():
    print(row)

connection.close()