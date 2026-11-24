
from pathlib import Path
from collections import defaultdict
import pandas as pd
import streamlit as st

PROJECT = Path(__file__).resolve().parents[2]
GTFS = PROJECT / "data" / "static_gtfs" / "extracted"


@st.cache_data
def load_raptor_data():

    print("Loading GTFS for RAPTOR engine...")

    stop_times = pd.read_parquet(
        PROJECT / "data" / "processed" /
        "transfer_stop_times.parquet"
    )

    trips = pd.read_csv(
        GTFS / "trips.txt",
        dtype={"trip_id": str, "route_id": str}
    )

    routes = pd.read_csv(
        GTFS / "routes.txt",
        dtype={"route_id": str}
    )

    stops = pd.read_csv(
        GTFS / "stops.txt",
        dtype={"stop_id": str}
    )

    trip_route = trips.set_index("trip_id")["route_id"].to_dict()

    route_names = routes.set_index("route_id")[
        "route_short_name"
    ].to_dict()

    stop_names = stops.set_index("stop_id")[
        "stop_name"
    ].to_dict()

    print("Building route patterns...")

    patterns = defaultdict(list)

    for trip_id, group in stop_times.groupby(
        "trip_id", sort=False
    ):

        group = group.sort_values("stop_sequence")
        stop_ids = tuple(group["stop_id"].astype(str))

        route_id = trip_route.get(str(trip_id))

        if route_id is None:
            continue

        pattern_key = (route_id, stop_ids)

        patterns[pattern_key].append({
            "trip_id": str(trip_id),
            "departures": group["departure_seconds"].to_numpy(),
            "arrivals": group["arrival_seconds"].to_numpy(),
            "departure_text": group["departure_time"].tolist(),
            "arrival_text": group["arrival_time"].tolist()
        })

    stop_patterns = defaultdict(list)
    final_patterns = []

    for (route_id, stop_ids), trips_in_pattern in patterns.items():

        trips_in_pattern.sort(
            key=lambda x: x["departures"][0]
        )

        pattern_index = len(final_patterns)

        final_patterns.append({
            "route_id": route_id,
            "stop_ids": stop_ids,
            "trips": trips_in_pattern
        })

        for position, stop_id in enumerate(stop_ids):
            stop_patterns[stop_id].append(
                (pattern_index, position)
            )

    print("RAPTOR patterns:", len(final_patterns))
    print("Indexed stops:", len(stop_patterns))

    return {
        "patterns": final_patterns,
        "stop_patterns": stop_patterns,
        "stop_names": stop_names,
        "route_names": route_names
    }


def find_raptor_journeys(
    data,
    origin,
    destination,
    start_time,
    max_transfers=1,
    transfer_buffer=300
):

    patterns = data["patterns"]
    stop_patterns = data["stop_patterns"]
    stop_names = data["stop_names"]
    route_names = data["route_names"]

    origin = str(origin)
    destination = str(destination)

    results = {}

    def make_leg(pattern, trip, board_pos, alight_pos):

        board_stop = pattern["stop_ids"][board_pos]
        alight_stop = pattern["stop_ids"][alight_pos]

        return {
            "route": route_names.get(pattern["route_id"], "Unknown"),
            "route_id": pattern["route_id"],
            "trip_id": trip["trip_id"],
            "from_stop": board_stop,
            "from_name": stop_names.get(board_stop, board_stop),
            "to_stop": alight_stop,
            "to_name": stop_names.get(alight_stop, alight_stop),
            "departure": trip["departure_text"][board_pos],
            "arrival": trip["arrival_text"][alight_pos],
            "departure_seconds": int(trip["departures"][board_pos]),
            "arrival_seconds": int(trip["arrivals"][alight_pos])
        }

    # STEP 1: Find direct journeys and first bus legs

    first_legs = []

    print("\n========== RAPTOR DIAGNOSTICS ==========")
    print("Origin:", origin)
    print("Destination:", destination)
    print("Start time:", start_time)
    print("Origin patterns:", len(stop_patterns.get(origin, [])))
    print("Destination patterns:", len(stop_patterns.get(destination, [])))


    print("\n--- ORIGIN PATTERN DETAILS ---")

    for pattern_index, origin_pos in stop_patterns.get(origin, []):

        pattern = patterns[pattern_index]

        print("Pattern index:", pattern_index)
        print("Route:", route_names.get(pattern["route_id"], "Unknown"))
        print("Total stops:", len(pattern["stop_ids"]))
        print("Origin position:", origin_pos)

        print("Stops after origin:")

        for stop_id in pattern["stop_ids"][origin_pos:origin_pos + 20]:
            print(stop_id, stop_names.get(stop_id, "Unknown"))

    print("\n--- DESTINATION PATTERN DETAILS ---")

    for pattern_index, destination_pos in stop_patterns.get(destination, []):

        pattern = patterns[pattern_index]

        print("Pattern index:", pattern_index)
        print("Route:", route_names.get(pattern["route_id"], "Unknown"))
        print("Destination position:", destination_pos)

        print("Stops before destination:")

        for stop_id in pattern["stop_ids"][:destination_pos + 1]:
            print(stop_id, stop_names.get(stop_id, "Unknown"))

    print("--- END PATTERN DETAILS ---\n")


    for pattern_index, origin_pos in stop_patterns.get(origin, []):

        pattern = patterns[pattern_index]
        stop_ids = pattern["stop_ids"]

        for trip in pattern["trips"]:

            departure = int(trip["departures"][origin_pos])

            if departure < start_time:
                continue

            for alight_pos in range(origin_pos + 1, len(stop_ids)):

                alight_stop = stop_ids[alight_pos]
                arrival = int(trip["arrivals"][alight_pos])

                if arrival <= departure:
                    continue

                leg = make_leg(
                    pattern, trip, origin_pos, alight_pos
                )

                if alight_stop == destination:

                    key = (trip["trip_id"],)

                    results[key] = {
                        "legs": [leg],
                        "arrival_seconds": arrival,
                        "total_minutes": (arrival - departure) / 60,
                        "waiting_minutes": (departure - start_time) / 60,
                        "transfers": 0
                    }

                else:
                    first_legs.append(leg)

    print("First-leg candidates:", len(first_legs))
    print("Direct journeys found:", len(results))
        # DIAGNOSTIC: Check possible transfer-stop overlap

    print("\n--- TRANSFER OVERLAP CHECK ---")

    first_leg_stops = set(
        leg["to_stop"] for leg in first_legs
    )

    print("Unique first-leg alighting stops:", len(first_leg_stops))

    destination_pattern_stops = set()

    for pattern_index, destination_pos in stop_patterns.get(destination, []):

        pattern = patterns[pattern_index]

        print("\nDestination pattern route:",
              route_names.get(pattern["route_id"], "Unknown"))

        print("Destination pattern trip count:",
              len(pattern["trips"]))

        print("Destination position:", destination_pos)

        # Only stops before destination can be transfer points.
        possible_stops = pattern["stop_ids"][:destination_pos]

        destination_pattern_stops.update(possible_stops)

        print("Stops before destination:", len(possible_stops))

    common_stops = first_leg_stops.intersection(
        destination_pattern_stops
    )

    print("Common possible transfer stops:", len(common_stops))

    for stop_id in list(common_stops)[:15]:
        print(
            stop_id,
            stop_names.get(stop_id, "Unknown stop")
        )

    print("--- END OVERLAP CHECK ---\n")

    # STEP 2: Find connecting second buses

    transfer_candidates = 0

    if max_transfers >= 1:

        for first_leg in first_legs:

            transfer_stop = first_leg["to_stop"]

            earliest_second_departure = (
                first_leg["arrival_seconds"] + transfer_buffer
            )

            for pattern_index, board_pos in stop_patterns.get(
                transfer_stop, []
            ):

                second_pattern = patterns[pattern_index]
                second_stop_ids = second_pattern["stop_ids"]

                destination_positions = [
                    pos for pos in range(
                        board_pos + 1, len(second_stop_ids)
                    )
                    if second_stop_ids[pos] == destination
                ]

                if not destination_positions:
                    continue

                best_trip = None
                best_departure = None
                best_destination_pos = None
                best_arrival = None

                for second_trip in second_pattern["trips"]:

                    if second_trip["trip_id"] == first_leg["trip_id"]:
                        continue

                    departure = int(
                        second_trip["departures"][board_pos]
                    )

                    if departure < earliest_second_departure:
                        continue

                    for destination_pos in destination_positions:

                        arrival = int(
                            second_trip["arrivals"][destination_pos]
                        )

                        if arrival <= departure:
                            continue

                        if (
                            best_departure is None
                            or departure < best_departure
                        ):
                            best_trip = second_trip
                            best_departure = departure
                            best_destination_pos = destination_pos
                            best_arrival = arrival

                if best_trip is None:
                    continue

                second_leg = make_leg(
                    second_pattern,
                    best_trip,
                    board_pos,
                    best_destination_pos
                )

                key = (
                    first_leg["trip_id"],
                    transfer_stop,
                    best_trip["trip_id"]
                )

                first_departure = first_leg["departure_seconds"]

                results[key] = {
                    "legs": [first_leg, second_leg],
                    "arrival_seconds": best_arrival,
                    "total_minutes": (
                        best_arrival - first_departure
                    ) / 60,
                    "waiting_minutes": (
                        first_departure - start_time
                    ) / 60,
                    "transfers": 1
                }

                transfer_candidates += 1

    print("Transfer journeys found:", transfer_candidates)
    print("Total journeys before filtering:", len(results))
    print("========== END DIAGNOSTICS ==========\n")

    final_results = sorted(
        results.values(),
        key=lambda x: x["arrival_seconds"]
    )

    return [
        journey for journey in final_results
        if journey["transfers"] == 1
    ][:10]
