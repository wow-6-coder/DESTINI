
from pathlib import Path
from bisect import bisect_left

import pandas as pd
import streamlit as st


PROJECT = Path(__file__).resolve().parents[1]
GTFS = PROJECT / "data" / "static_gtfs" / "extracted"
PROCESSED = PROJECT / "data" / "processed"


@st.cache_data
def load_transfer_data():

    print("Loading prepared transfer data...")

    stop_times = pd.read_parquet(
        PROCESSED / "transfer_stop_times.parquet"
    )

    stops = pd.read_csv(
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

    trip_route = trips.merge(
        routes[["route_id", "route_short_name"]],
        on="route_id",
        how="left"
    ).set_index("trip_id")["route_short_name"]

    stop_name_lookup = stops.set_index(
        "stop_id"
    )["stop_name"]

    print("Transfer data loaded:", len(stop_times))

    return stop_times, trip_route, stop_name_lookup


def find_transfer_journeys(
    stop_times,
    trip_route,
    stop_name_lookup,
    origin,
    destination,
    start_time
):

    print("Starting corrected transfer search...")

    # Ensure stop IDs use the same format.
    origin = str(origin)
    destination = str(destination)

    # Build trip index.
    by_trip = {
        str(trip_id): group
        for trip_id, group in stop_times.groupby(
            "trip_id", sort=False
        )
    }

    # Build departure index, sorted by departure time.
    by_stop = {}

    for stop_id, group in stop_times.groupby(
        "stop_id", sort=False
    ):

        group = group.sort_values(
            "departure_seconds"
        ).reset_index(drop=True)

        departure_times = group[
            "departure_seconds"
        ].tolist()

        by_stop[str(stop_id)] = (
            group,
            departure_times
        )

    # Index destination records by trip.
    destination_by_trip = {}

    destination_rows = stop_times[
        stop_times["stop_id"].astype(str) == destination
    ]

    for trip_id, group in destination_rows.groupby(
        "trip_id", sort=False
    ):

        destination_by_trip[str(trip_id)] = group

    # Find first buses departing from origin.
    first_departures = stop_times[
        (stop_times["stop_id"].astype(str) == origin) &
        (stop_times["departure_seconds"] >= start_time)
    ]

    print("First buses found:", len(first_departures))
    print("Trips serving destination:", len(destination_by_trip))

    results = []
    checked = set()

    # Iterate through first buses.
    for first_start in first_departures.itertuples(
        index=False
    ):

        first_trip_id = str(first_start.trip_id)

        first_trip = by_trip.get(first_trip_id)

        if first_trip is None:
            continue

        transfer_stops = first_trip[
            first_trip["stop_sequence"] >
            first_start.stop_sequence
        ]

        for transfer in transfer_stops.itertuples(
            index=False
        ):

            transfer_id = str(transfer.stop_id)

            if transfer_id == destination:
                continue

            earliest_second_bus = (
                transfer.arrival_seconds + 300
            )

            stop_entry = by_stop.get(transfer_id)

            if stop_entry is None:
                continue

            second_group, departure_times = stop_entry

            # Binary search: skip buses departing too early.
            position = bisect_left(
                departure_times,
                earliest_second_bus
            )

            eligible_buses = second_group.iloc[position:]

            for second_start in eligible_buses.itertuples(
                index=False
            ):

                second_trip_id = str(second_start.trip_id)

                if second_trip_id == first_trip_id:
                    continue

                key = (
                    first_trip_id,
                    transfer_id,
                    second_trip_id
                )

                if key in checked:
                    continue

                checked.add(key)

                # Check whether this second bus reaches destination
                # AFTER boarding at the transfer stop.
                destination_group = destination_by_trip.get(
                    second_trip_id
                )

                if destination_group is None:
                    continue

                valid_destinations = destination_group[
                    destination_group["stop_sequence"] >
                    second_start.stop_sequence
                ]

                if valid_destinations.empty:
                    continue

                # Preserve the original earliest-arrival selection.
                end = valid_destinations.loc[
                    valid_destinations["arrival_seconds"].idxmin()
                ]

                if (
                    end["arrival_seconds"] <=
                    first_start.departure_seconds
                ):
                    continue

                results.append({
                    "first_route": trip_route.get(
                        first_trip_id, "Unknown"
                    ),
                    "first_trip": first_trip_id,
                    "departure": first_start.departure_time,
                    "transfer_stop": transfer_id,
                    "transfer_name": stop_name_lookup.get(
                        transfer_id, "Unknown"
                    ),
                    "second_route": trip_route.get(
                        second_trip_id, "Unknown"
                    ),
                    "second_trip": second_trip_id,
                    "second_departure": second_start.departure_time,
                    "arrival": end["arrival_time"],
                    "total_minutes": (
                        end["arrival_seconds"] -
                        first_start.departure_seconds
                    ) / 60
                })

    results.sort(
        key=lambda x: x["total_minutes"]
    )

    print("Corrected transfer search completed.")
    print("Valid journeys found:", len(results))

    return results[:5]

