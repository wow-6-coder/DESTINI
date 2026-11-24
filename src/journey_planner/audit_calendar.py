import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT / "data" / "static_gtfs" / "extracted"

trips = pd.read_csv(
    DATA_DIR / "trips.txt",
    dtype=str
)

calendar = pd.read_csv(
    DATA_DIR / "calendar.txt",
    dtype=str
)

print("\n========== SERVICE CALENDAR AUDIT ==========")

print("Total trips:", len(trips))
print("Unique service IDs in trips:", trips["service_id"].nunique())

print("Calendar records:", len(calendar))
print("Unique service IDs in calendar:", calendar["service_id"].nunique())

# Check whether every trip has a calendar entry
missing = set(trips["service_id"]) - set(calendar["service_id"])

print("\nService IDs missing from calendar:", len(missing))
if missing:
    print(missing)

# Check duplicate calendar entries
print(
    "Duplicate service IDs:",
    calendar["service_id"].duplicated().sum()
)

# Check operating days
days = [
    "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday"
]

print("\nOperating-day patterns:")
print(calendar[days].value_counts().to_string())

print("\nCalendar date range:")
print("Start:", calendar["start_date"].min())
print("End:", calendar["end_date"].max())

print("============================================")
