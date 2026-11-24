import csv
from pathlib import Path

p = Path("data/static_gtfs/extracted")

def read_ids(filename, column):
    with open(p / filename, encoding="utf-8-sig", newline="") as f:
        return {row[column] for row in csv.DictReader(f)}

stops = read_ids("stops.txt", "stop_id")
routes = read_ids("routes.txt", "route_id")
trips = read_ids("trips.txt", "trip_id")

stop_time_rows = 0
unknown_stops = set()
unknown_trips = set()

with open(p / "stop_times.txt", encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        stop_time_rows += 1
        if row["stop_id"] not in stops:
            unknown_stops.add(row["stop_id"])
        if row["trip_id"] not in trips:
            unknown_trips.add(row["trip_id"])

print("\n========== GTFS DATA AUDIT ==========")
print("Unique stops:", len(stops))
print("Routes:", len(routes))
print("Trips:", len(trips))
print("Stop-time records:", stop_time_rows)
print("Unknown stop IDs:", len(unknown_stops))
print("Unknown trip IDs:", len(unknown_trips))
print("====================================")
