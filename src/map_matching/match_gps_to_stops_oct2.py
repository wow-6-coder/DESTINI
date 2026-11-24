
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

GPS_FILE = PROJECT / "data" / "processed" / "matched_gps_764_oct2.csv"
STOPS_FILE = PROJECT / "data" / "static_gtfs" / "extracted" / "stops.txt"

OUTPUT = PROJECT / "data" / "processed" / "gps_stop_matches_764_oct2.csv"

print("Loading October 2 GPS observations...")
gps = pd.read_csv(GPS_FILE)

print("Loading GTFS bus stops...")
stops = pd.read_csv(STOPS_FILE)

gps["lat"] = pd.to_numeric(gps["lat"], errors="coerce")
gps["lng"] = pd.to_numeric(gps["lng"], errors="coerce")

stops["stop_lat"] = pd.to_numeric(stops["stop_lat"], errors="coerce")
stops["stop_lon"] = pd.to_numeric(stops["stop_lon"], errors="coerce")

gps = gps.dropna(subset=["lat", "lng"]).reset_index(drop=True)
stops = stops.dropna(subset=["stop_lat", "stop_lon"]).reset_index(drop=True)

stop_lat = stops["stop_lat"].to_numpy()
stop_lon = stops["stop_lon"].to_numpy()

matched_results = []

batch_size = 300

print("Matching GPS points to nearest stops...")

for start in range(0, len(gps), batch_size):
    end = min(start + batch_size, len(gps))
    batch = gps.iloc[start:end]

    lat = batch["lat"].to_numpy()
    lon = batch["lng"].to_numpy()

    dy = (lat[:, None] - stop_lat[None, :]) * 111320

    dx = (
        (lon[:, None] - stop_lon[None, :])
        * 111320
        * np.cos(np.radians(lat[:, None]))
    )

    distances = np.sqrt(dx**2 + dy**2)

    nearest_indices = np.argmin(distances, axis=1)
    nearest_distances = distances[
        np.arange(len(batch)), nearest_indices
    ]

    result = batch.copy().reset_index(drop=True)

    result["nearest_stop_id"] = stops.iloc[
        nearest_indices
    ]["stop_id"].to_numpy()

    result["nearest_stop_name"] = stops.iloc[
        nearest_indices
    ]["stop_name"].to_numpy()

    result["distance_m"] = nearest_distances

    matched_results.append(result)

    if end % 3000 == 0 or end == len(gps):
        print(f"Processed {end}/{len(gps)}")

matched = pd.concat(matched_results, ignore_index=True)

matched["is_matched"] = matched["distance_m"] <= 150

matched.to_csv(OUTPUT, index=False)

print("\n========== OCTOBER 2 MATCHING REPORT ==========")
print("Total GPS points:", len(matched))
print("Matched within 150m:", matched["is_matched"].sum())
print("Match percentage:", round(matched["is_matched"].mean() * 100, 2), "%")
print("Unique matched stops:", matched.loc[matched["is_matched"], "nearest_stop_id"].nunique())
print("Average matched distance:", round(matched.loc[matched["is_matched"], "distance_m"].mean(), 2), "metres")
print("Output:", OUTPUT)
