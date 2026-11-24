
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
DATA = PROJECT / "data" / "processed"

print("Loading connections...")

df = pd.read_csv(
    DATA / "bus_connections_enriched.csv",
    dtype={"from_stop": str, "to_stop": str}
)

gps = pd.read_csv(
    DATA / "route_764_integrated_estimates.csv",
    dtype={"from_stop": str, "to_stop": str}
)

gps_lookup = {
    (str(row["from_stop"]), str(row["to_stop"])):
    float(row["estimated_minutes"])
    for _, row in gps.iterrows()
}


def find_stop(name):
    from_matches = df[
        df["from_stop_name"].str.contains(
            name, case=False, na=False
        )
    ][["from_stop", "from_stop_name"]].rename(
        columns={"from_stop": "stop_id",
                 "from_stop_name": "stop_name"}
    )

    to_matches = df[
        df["to_stop_name"].str.contains(
            name, case=False, na=False
        )
    ][["to_stop", "to_stop_name"]].rename(
        columns={"to_stop": "stop_id",
                 "to_stop_name": "stop_name"}
    )

    matches = pd.concat(
        [from_matches, to_matches]
    ).drop_duplicates(subset=["stop_id"])

    return matches


origin_name = input("Starting stop: ").strip()
destination_name = input("Destination stop: ").strip()
departure = input("Departure time (HH:MM): ").strip()

try:
    hour, minute = map(int, departure.split(":"))
    departure_seconds = hour * 3600 + minute * 60
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise ValueError
except ValueError:
    raise SystemExit("Invalid time. Use HH:MM.")

# Exact stop IDs for this GPS validation test
if origin_name == "OS Communication":
    origin_matches = pd.DataFrame([{
        "stop_id": "10062",
        "stop_name": "OS Communication"
    }])
else:
    origin_matches = find_stop(origin_name)

if destination_name == "Greater Kailash$":
    destination_matches = pd.DataFrame([{
        "stop_id": "10083",
        "stop_name": "Greater Kailash"
    }])
else:
    destination_matches = find_stop(destination_name)

if len(origin_matches) != 1 or len(destination_matches) != 1:
    print("\nCould not identify both stops uniquely.")
    print("\nStarting stop matches:")
    print(origin_matches.to_string(index=False))
    print("\nDestination stop matches:")
    print(destination_matches.to_string(index=False))
    raise SystemExit("Try a more specific stop name.")

origin_id = origin_matches.iloc[0]["stop_id"]
destination_id = destination_matches.iloc[0]["stop_id"]

print("\nOrigin:", origin_matches.iloc[0]["stop_name"])
print("Destination:", destination_matches.iloc[0]["stop_name"])

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
    (direct["stop_sequence_end"] >= direct["stop_sequence_start"]) &
    (direct["arrival_seconds_end"] >=
     direct["departure_seconds_start"])
]

def calculate_estimate(row):
    route = str(row["route_short_name_start"]).strip()

    scheduled = (
        row["arrival_seconds_end"] -
        row["departure_seconds_start"]
    ) / 60

    if route != "764DOWN":
        return scheduled, "Schedule only"

    if row["stop_sequence_start"] == row["stop_sequence_end"]:
            segments = df[
                (df["trip_id"] == row["trip_id"]) &
                (df["stop_sequence"] == row["stop_sequence_start"])
            ].sort_values("stop_sequence")
    else:
            segments = df[
                (df["trip_id"] == row["trip_id"]) &
                (df["stop_sequence"] >= row["stop_sequence_start"]) &
                (df["stop_sequence"] < row["stop_sequence_end"])
            ].sort_values("stop_sequence")

    estimated = 0
    used_gps = False

    for _, segment in segments.iterrows():
        pair = (
            str(segment["from_stop"]),
            str(segment["to_stop"])
        )

        if pair in gps_lookup:
            estimated += gps_lookup[pair]
            used_gps = True
        else:
            estimated += segment["travel_time_seconds"] / 60

    return estimated, (
        "GPS + Schedule" if used_gps else "Schedule only"
    )


direct = direct.sort_values("arrival_seconds_end")

print("\n========== DIRECT JOURNEYS ==========")

if direct.empty:
    print("No direct journey found.")
else:
    for _, row in direct.head(5).iterrows():
        scheduled = (
            row["arrival_seconds_end"] -
            row["departure_seconds_start"]
        ) / 60

        estimated, source = calculate_estimate(row)

        estimated_arrival = (
            row["departure_seconds_start"] +
            estimated * 60
        )

        estimated_hour = int(estimated_arrival // 3600) % 24
        estimated_minute = int((estimated_arrival % 3600) // 60)
        estimated_second = int(estimated_arrival % 60)

        print("\nRoute:", row["route_short_name_start"])
        print("Trip:", row["trip_id"])
        print("Departure:", row["departure_time_start"])
        print("Scheduled arrival:", row["arrival_time_end"])
        print("Estimated arrival:",
              f"{estimated_hour:02d}:{estimated_minute:02d}:{estimated_second:02d}")
        print("Scheduled duration:", round(scheduled, 1), "minutes")
        print("Estimated duration:", round(estimated, 1), "minutes")
        print("Estimate source:", source)

print("\n=====================================")
