
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
FILE = PROJECT / "data" / "processed" / "bus_connections_enriched.csv"

df = pd.read_csv(FILE)

origin = "Shivam Apartment Vikas Puri"

matches = df[
    df["from_stop_name"].str.lower().eq(origin.lower())
].copy()

matches = matches[
    matches["departure_seconds"] >= 8 * 3600 + 30 * 60
]

matches = matches.sort_values("departure_seconds")

print("\nDEPARTURES AFTER 08:30")
print(
    matches[
        ["departure_time", "route_short_name",
         "to_stop_name", "trip_id"]
    ].drop_duplicates().head(20).to_string(index=False)
)

print("\nTotal matching connections:", len(matches))
