
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

DATA_FILE = PROJECT / "data" / "processed" / "bus_connections_enriched.csv"

print("Loading connections...")

df = pd.read_csv(
    DATA_FILE,
    usecols=[
        "trip_id", "from_stop", "to_stop",
        "departure_time", "arrival_time",
        "departure_seconds", "arrival_seconds",
        "stop_sequence", "route_short_name",
        "from_stop_name", "to_stop_name"
    ],
    dtype={"from_stop": str, "to_stop": str}
)

def find_stop(name, column):
    matches = df[
        df[column].str.contains(name, case=False, na=False)
    ]

    return matches.drop_duplicates(
        subset=["from_stop" if column == "from_stop_name" else "to_stop"]
    )

print("\nAvailable stops are searched by name.")

origin_name = input("Starting stop: ").strip()
destination_name = input("Destination stop: ").strip()
departure = input("Departure time (HH:MM): ").strip()

try:
    hour, minute = map(int, departure.split(":"))
    departure_seconds = hour * 3600 + minute * 60
except ValueError:
    raise SystemExit("Invalid time. Use HH:MM, for example 08:30.")

origin_matches = find_stop(origin_name, "from_stop_name")
destination_matches = find_stop(destination_name, "to_stop_name")

if len(origin_matches) != 1 or len(destination_matches) != 1:
    print("\nCould not identify both stops uniquely.")
    print("\nStarting stop matches:")
    print(origin_matches[["from_stop", "from_stop_name"]].head(10))
    print("\nDestination stop matches:")
    print(destination_matches[["to_stop", "to_stop_name"]].head(10))
    raise SystemExit("Try a more specific stop name.")

origin_id = origin_matches.iloc[0]["from_stop"]
destination_id = destination_matches.iloc[0]["to_stop"]

print("\nOrigin:", origin_matches.iloc[0]["from_stop_name"])
print("Destination:", destination_matches.iloc[0]["to_stop_name"])

# Find direct journeys
origin_edges = df[
    (df["from_stop"] == origin_id) &
    (df["departure_seconds"] >= departure_seconds)
]

destination_edges = df[
    df["to_stop"] == destination_id
]

direct = origin_edges.merge(
    destination_edges,
    on="trip_id",
    suffixes=("_start", "_end")
)

direct = direct[
    direct["stop_sequence_end"] >= direct["stop_sequence_start"]
]

direct = direct[
    direct["arrival_seconds_end"] >=
    direct["departure_seconds_start"]
]

direct = direct.sort_values("arrival_seconds_end")

print("\n========== DIRECT JOURNEYS ==========")

if direct.empty:
    print("No direct journey found.")
else:
    for _, row in direct.head(5).iterrows():
        duration = (
            row["arrival_seconds_end"] -
            row["departure_seconds_start"]
        )

        print("\nRoute:", row["route_short_name_start"])
        print("Trip:", row["trip_id"])
        print("Departure:", row["departure_time_start"])
        print("Arrival:", row["arrival_time_end"])
        print("Travel time:", round(duration / 60, 1), "minutes")

print("\n=====================================")
