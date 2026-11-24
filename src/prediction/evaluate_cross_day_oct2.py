
from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parents[2]

OCT1_GPS = BASE / "data/processed/gps_travel_times_764.csv"
OCT2_GPS = BASE / "data/processed/gps_travel_times_764_oct2.csv"

GTFS_DIR = BASE / "data/static_gtfs/extracted"

OUTPUT = BASE / "reports/oct2_cross_day_predictions.csv"
SUMMARY = BASE / "reports/oct2_cross_day_summary.csv"


def time_to_seconds(value):
    """Convert GTFS HH:MM:SS to seconds, including times beyond 24:00."""
    if pd.isna(value):
        return np.nan

    try:
        parts = str(value).split(":")
        return (
            int(parts[0]) * 3600
            + int(parts[1]) * 60
            + float(parts[2])
        )
    except (ValueError, IndexError):
        return np.nan


def calculate_metrics(actual, predicted):
    errors = np.asarray(predicted) - np.asarray(actual)

    return {
        "MAE_seconds": np.mean(np.abs(errors)),
        "RMSE_seconds": np.sqrt(np.mean(errors ** 2))
    }


print("\nLoading October 1 training GPS data...")
oct1 = pd.read_csv(OCT1_GPS)

print("Loading October 2 independent test GPS data...")
oct2 = pd.read_csv(OCT2_GPS)

print("Loading original GTFS timetable...")

trips = pd.read_csv(
    GTFS_DIR / "trips.txt",
    dtype=str
)

stop_times = pd.read_csv(
    GTFS_DIR / "stop_times.txt",
    dtype=str
)

# --------------------------------------------------
# 1. Prepare October 1 GPS training observations
# --------------------------------------------------

for df in [oct1, oct2]:
    df["from_stop_id"] = df["from_stop_id"].astype(str)
    df["to_stop_id"] = df["to_stop_id"].astype(str)

    df["travel_seconds"] = pd.to_numeric(
        df["travel_seconds"],
        errors="coerce"
    )

oct1 = oct1.dropna(
    subset=["from_stop_id", "to_stop_id", "travel_seconds"]
)

oct2 = oct2.dropna(
    subset=["from_stop_id", "to_stop_id", "travel_seconds"]
)

# Learn one GPS median per stop pair from October 1 only.
gps_model = (
    oct1.groupby(["from_stop_id", "to_stop_id"])["travel_seconds"]
    .median()
    .rename("oct1_gps_median")
    .reset_index()
)

# --------------------------------------------------
# 2. Build schedule-only baseline from original GTFS
# --------------------------------------------------

route_trips = trips[
    trips["route_id"] == "2229"
][["trip_id", "route_id"]].copy()

stop_times = stop_times.merge(
    route_trips,
    on="trip_id",
    how="inner"
)

stop_times["stop_sequence"] = pd.to_numeric(
    stop_times["stop_sequence"],
    errors="coerce"
)

stop_times["departure_seconds"] = (
    stop_times["departure_time"].apply(time_to_seconds)
)

stop_times["arrival_seconds"] = (
    stop_times["arrival_time"].apply(time_to_seconds)
)

stop_times = stop_times.dropna(
    subset=[
        "trip_id",
        "stop_id",
        "stop_sequence",
        "departure_seconds",
        "arrival_seconds"
    ]
)

stop_times = stop_times.sort_values(
    ["trip_id", "stop_sequence"]
)

stop_times["next_stop_id"] = (
    stop_times.groupby("trip_id")["stop_id"].shift(-1)
)

stop_times["next_arrival_seconds"] = (
    stop_times.groupby("trip_id")["arrival_seconds"].shift(-1)
)

stop_times["next_sequence"] = (
    stop_times.groupby("trip_id")["stop_sequence"].shift(-1)
)

stop_times["scheduled_seconds"] = (
    stop_times["next_arrival_seconds"]
    - stop_times["departure_seconds"]
)

stop_times["sequence_gap"] = (
    stop_times["next_sequence"] - stop_times["stop_sequence"]
)

schedule_segments = stop_times[
    (stop_times["sequence_gap"] == 1) &
    (stop_times["scheduled_seconds"] > 0) &
    (stop_times["scheduled_seconds"] <= 1800)
].copy()

schedule_model = (
    schedule_segments.groupby(
        ["stop_id", "next_stop_id"]
    )["scheduled_seconds"]
    .median()
    .rename("scheduled_seconds")
    .reset_index()
)

schedule_model = schedule_model.rename(
    columns={
        "stop_id": "from_stop_id",
        "next_stop_id": "to_stop_id"
    }
)

# --------------------------------------------------
# 3. Predict October 2 using October 1 only
# --------------------------------------------------

print("\nBuilding October 1 prediction model...")

test = oct2.merge(
    gps_model,
    on=["from_stop_id", "to_stop_id"],
    how="left"
)

test = test.merge(
    schedule_model,
    on=["from_stop_id", "to_stop_id"],
    how="inner"
)

if test.empty:
    raise ValueError(
        "No October 2 observations matched both the GPS model "
        "and original GTFS schedule."
    )

test["gps_covered"] = test["oct1_gps_median"].notna()

# GPS-only model with schedule fallback.
test["model_prediction_seconds"] = np.where(
    test["gps_covered"],
    test["oct1_gps_median"],
    test["scheduled_seconds"]
)

test["prediction_source"] = np.where(
    test["gps_covered"],
    "October 1 GPS",
    "Schedule fallback"
)

# --------------------------------------------------
# 4. Calculate final metrics
# --------------------------------------------------

actual = test["travel_seconds"]
schedule_prediction = test["scheduled_seconds"]
model_prediction = test["model_prediction_seconds"]

schedule_metrics = calculate_metrics(
    actual,
    schedule_prediction
)

model_metrics = calculate_metrics(
    actual,
    model_prediction
)

covered = test[test["gps_covered"]].copy()

covered_schedule_metrics = calculate_metrics(
    covered["travel_seconds"],
    covered["scheduled_seconds"]
) if len(covered) else None

covered_model_metrics = calculate_metrics(
    covered["travel_seconds"],
    covered["model_prediction_seconds"]
) if len(covered) else None

coverage = test["gps_covered"].mean() * 100

mae_improvement = (
    schedule_metrics["MAE_seconds"]
    - model_metrics["MAE_seconds"]
)

percentage_improvement = (
    mae_improvement / schedule_metrics["MAE_seconds"] * 100
    if schedule_metrics["MAE_seconds"] > 0
    else 0
)

print("\n" + "=" * 65)
print("ROUTE 764DOWN - CROSS-DAY EVALUATION")
print("TRAINING: OCTOBER 1 | TESTING: OCTOBER 2")
print("=" * 65)

print("\nDATASET")
print("October 1 GPS training observations:", len(oct1))
print("October 1 GPS stop pairs:", len(gps_model))
print("October 2 test observations:", len(oct2))
print("October 2 evaluated observations:", len(test))
print("Evaluated October 2 trips:", test["trip_id"].nunique())
print("Evaluated stop pairs:", test[
    ["from_stop_id", "to_stop_id"]
].drop_duplicates().shape[0])

print("\nGPS COVERAGE")
print("GPS-covered observations:", int(test["gps_covered"].sum()))
print("Schedule fallback observations:", int((~test["gps_covered"]).sum()))
print("GPS coverage:", round(coverage, 2), "%")

print("\n1. SCHEDULE-ONLY BASELINE")
print("MAE:", round(schedule_metrics["MAE_seconds"], 2), "seconds")
print("RMSE:", round(schedule_metrics["RMSE_seconds"], 2), "seconds")

print("\n2. OCTOBER 1 GPS MODEL + SCHEDULE FALLBACK")
print("MAE:", round(model_metrics["MAE_seconds"], 2), "seconds")
print("RMSE:", round(model_metrics["RMSE_seconds"], 2), "seconds")

print("\n3. IMPROVEMENT")
print("MAE improvement:", round(mae_improvement, 2), "seconds")
print("MAE improvement percentage:", round(percentage_improvement, 2), "%")

if covered_schedule_metrics is not None:
    print("\n4. COMPARISON ON GPS-COVERED OBSERVATIONS ONLY")
    print(
        "Schedule MAE:",
        round(covered_schedule_metrics["MAE_seconds"], 2),
        "seconds"
    )
    print(
        "GPS model MAE:",
        round(covered_model_metrics["MAE_seconds"], 2),
        "seconds"
    )

# --------------------------------------------------
# 5. Save detailed predictions and summary
# --------------------------------------------------

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

test.to_csv(OUTPUT, index=False)

summary = pd.DataFrame([
    {
        "model": "Schedule only",
        "observations": len(test),
        "MAE_seconds": schedule_metrics["MAE_seconds"],
        "RMSE_seconds": schedule_metrics["RMSE_seconds"],
        "GPS_coverage_percent": 0
    },
    {
        "model": "October 1 GPS + schedule fallback",
        "observations": len(test),
        "MAE_seconds": model_metrics["MAE_seconds"],
        "RMSE_seconds": model_metrics["RMSE_seconds"],
        "GPS_coverage_percent": coverage
    }
])

summary.to_csv(SUMMARY, index=False)

print("\nREPORTS SAVED")
print(OUTPUT)
print(SUMMARY)

print("\nCross-day evaluation completed.")
