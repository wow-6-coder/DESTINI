
from raptor_engine import (
    load_raptor_data,
    find_raptor_journeys
)

import pandas as pd
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
GTFS = PROJECT / "data" / "static_gtfs" / "extracted"


def select_stop(data, prompt):

    stops = pd.read_csv(
        GTFS / "stops.txt",
        dtype={"stop_id": str}
    )

    while True:

        name = input(prompt).strip()

        matches = stops[
            stops["stop_name"].str.contains(
                name,
                case=False,
                na=False,
                regex=False
            )
        ][["stop_id", "stop_name"]].drop_duplicates()

        if matches.empty:
            print("No matching stops. Try again.")
            continue

        print("\nMatching stops:")
        print(matches.to_string(index=False))

        valid_ids = set(matches["stop_id"].astype(str))

        while True:

            stop_id = input("\nEnter Stop ID: ").strip()

            if stop_id in valid_ids:
                print("Selected:", matches[
                    matches["stop_id"] == stop_id
                ]["stop_name"].iloc[0])
                return stop_id

            print("Invalid ID. Select an ID from the list.")


print("Loading RAPTOR engine...")
data = load_raptor_data()

print("\n========== JOURNEY SEARCH ==========")

origin = select_stop(data, "Starting stop name: ")
destination = select_stop(data, "Destination stop name: ")

if origin == destination:
    raise SystemExit("Origin and destination cannot be the same.")

departure = input("Departure time (HH:MM): ").strip()

try:
    hour, minute = map(int, departure.split(":"))

    if not (0 <= hour <= 47 and 0 <= minute <= 59):
        raise ValueError

    start_time = hour * 3600 + minute * 60

except ValueError:
    raise SystemExit("Enter a valid time, e.g. 05:00.")

print("\nSearching using RAPTOR...")

start = time.perf_counter()

results = find_raptor_journeys(
    data=data,
    origin=origin,
    destination=destination,
    start_time=start_time,
    max_transfers=1,
    transfer_buffer=300
)

elapsed = time.perf_counter() - start

print("\n========== RAPTOR RESULTS ==========")
print("Search time:", round(elapsed, 3), "seconds")
print("Journeys found:", len(results))

if not results:
    print("No journeys found.")

for number, journey in enumerate(results, 1):

    print(f"\nOPTION {number}")
    print("Transfers:", journey["transfers"])
    print("Journey duration:", round(
        journey["total_minutes"], 2
    ), "minutes")

    for leg_number, leg in enumerate(journey["legs"], 1):

        print(f"\nLeg {leg_number}")
        print("Bus route:", leg["route"])
        print("Trip ID:", leg["trip_id"])
        print("Board:", leg["from_name"], "| ID:", leg["from_stop"])
        print("Departure:", leg["departure"])
        print("Alight:", leg["to_name"], "| ID:", leg["to_stop"])
        print("Arrival:", leg["arrival"])

print("\n====================================")
