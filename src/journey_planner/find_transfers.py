
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
GTFS = PROJECT / "data" / "static_gtfs" / "extracted"

print("Loading GTFS data...")

st = pd.read_parquet(
    PROJECT / "data" / "processed" / "transfer_stop_times.parquet"
)

stop_names = pd.read_csv(
    GTFS / "stops.txt",
    dtype={"stop_id": str}
)

trips = pd.read_csv(
    GTFS / "trips.txt",
    dtype={"trip_id": str, "route_id": str}
)

routes = pd.read_csv(
    GTFS / "routes.txt",
    dtype={"route_id": str}
)

# Convert GTFS times into seconds, including times beyond 24:00
def to_seconds(value):
    h, m, s = map(int, value.split(":"))
    return h * 3600 + m * 60 + s


# Prepare timetable data
if "departure_seconds" not in st.columns:
    st["departure_seconds"] = st["departure_time"].map(to_seconds)

if "arrival_seconds" not in st.columns:
    st["arrival_seconds"] = st["arrival_time"].map(to_seconds)

st["stop_sequence"] = pd.to_numeric(st["stop_sequence"])
st = st.sort_values(["trip_id", "stop_sequence"])


# Stop selection: search by name, then select using stop ID
def select_stop(prompt):

    while True:

        name = input(prompt).strip()

        if not name:
            print("Please enter a stop name.")
            continue

        matches = stop_names[
            stop_names["stop_name"].str.contains(
                name,
                case=False,
                na=False,
                regex=False
            )
        ][["stop_id", "stop_name"]].drop_duplicates()

        if matches.empty:
            print("No matching stops found. Try another name.")
            continue

        print("\nMatching stops:")
        print(
            matches.to_string(index=False)
        )

        valid_ids = set(matches["stop_id"].astype(str))

        while True:

            selected_id = input(
                "\nEnter the Stop ID from the list above: "
            ).strip()

            if selected_id in valid_ids:
                selected_name = matches.loc[
                    matches["stop_id"].astype(str) == selected_id,
                    "stop_name"
                ].iloc[0]

                print(
                    f"Selected: {selected_name} (ID: {selected_id})"
                )

                return selected_id

            print("Invalid Stop ID. Choose an ID from the displayed list.")


# Collect journey details
origin = select_stop("\nStarting stop name: ")

destination = select_stop("\nDestination stop name: ")

if origin == destination:
    raise SystemExit("Starting stop and destination cannot be the same.")

departure = input("\nDeparture time (HH:MM): ").strip()

try:
    hour, minute = map(int, departure.split(":"))

    if not (0 <= hour <= 47 and 0 <= minute <= 59):
        raise ValueError

    start_time = hour * 3600 + minute * 60

except ValueError:
    raise SystemExit("Enter a valid departure time, e.g. 08:30.")


# Prepare stop and route lookups
stop_name_lookup = (
    stop_names.drop_duplicates("stop_id")
    .set_index("stop_id")["stop_name"]
)

trip_routes = trips.merge(
    routes[["route_id", "route_short_name"]],
    on="route_id",
    how="left"
).set_index("trip_id")

trip_route = trip_routes["route_short_name"]
trip_route_id = trip_routes["route_id"]

# Group timetable data for faster lookup
by_trip = st.groupby("trip_id", sort=False)
by_stop = st.groupby("stop_id", sort=False)

first_departures = st[
    (st["stop_id"] == origin) &
    (st["departure_seconds"] >= start_time)
]

print("\nSearching for one-transfer journeys...")

results = []
checked = set()

for _, first_start in first_departures.iterrows():

    first_trip = by_trip.get_group(first_start["trip_id"])

    transfer_stops = first_trip[
        first_trip["stop_sequence"] > first_start["stop_sequence"]
    ]

    for _, transfer in transfer_stops.iterrows():

        transfer_id = transfer["stop_id"]
        earliest_second_bus = transfer["arrival_seconds"] + 300

        if transfer_id == destination:
            continue

        try:
            second_departures = by_stop.get_group(transfer_id)
        except KeyError:
            continue

        second_departures = second_departures[
            second_departures["departure_seconds"] >= earliest_second_bus
        ]

        for _, second_start in second_departures.iterrows():

            if second_start["trip_id"] == first_start["trip_id"]:
                continue

            key = (
                first_start["trip_id"],
                transfer_id,
                second_start["trip_id"]
            )

            if key in checked:
                continue

            checked.add(key)

            second_trip = by_trip.get_group(second_start["trip_id"])

            destination_rows = second_trip[
                (second_trip["stop_id"] == destination) &
                (second_trip["stop_sequence"] > second_start["stop_sequence"])
            ]

            if destination_rows.empty:
                continue

            end = destination_rows.sort_values(
                "arrival_seconds"
            ).iloc[0]

            if end["arrival_seconds"] <= first_start["departure_seconds"]:
                continue

            results.append({
                "first_route": trip_route.get(first_start["trip_id"], "Unknown"),
                "first_route_id": trip_route_id.get(first_start["trip_id"], "Unknown"),
                "first_trip": first_start["trip_id"],
                "departure": first_start["departure_time"],

                "transfer_stop": transfer_id,
                "transfer_name": stop_name_lookup.get(transfer_id, "Unknown"),

                "second_route": trip_route.get(second_start["trip_id"], "Unknown"),
                "second_route_id": trip_route_id.get(second_start["trip_id"], "Unknown"),
                "second_trip": second_start["trip_id"],
                "second_departure": second_start["departure_time"],

                "arrival": end["arrival_time"],
                "total_minutes": (
                    end["arrival_seconds"] -
                    first_start["departure_seconds"]
                ) / 60
            })


# Display results
print("\n========== ONE-TRANSFER RESULTS ==========")

if not results:
    print("No one-transfer journeys found.")

else:
    results.sort(key=lambda x: x["total_minutes"])

    for number, journey in enumerate(results[:5], 1):

        print(f"\nOPTION {number}")

        print(
            "First bus:",
            journey["first_route"],
            "| Route ID:", journey["first_route_id"]
        )

        print("First trip ID:", journey["first_trip"])
        print("Departure:", journey["departure"])

        print(
            "Transfer stop:",
            journey["transfer_name"],
            "| Stop ID:", journey["transfer_stop"]
        )

        print(
            "Second bus:",
            journey["second_route"],
            "| Route ID:", journey["second_route_id"]
        )

        print("Second trip ID:", journey["second_trip"])
        print("Second departure:", journey["second_departure"])
        print("Arrival:", journey["arrival"])

        print(
            "Total journey time:",
            round(journey["total_minutes"], 1),
            "minutes"
        )

print("\nTotal possible journeys found:", len(results))
print("==========================================")
