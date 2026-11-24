from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]

GPS_FILE = BASE / "data/processed/gps_travel_times_764.csv"
SCHEDULE_FILE = BASE / "data/processed/route_764_integrated_estimates.csv"
OUTPUT_FILE = BASE / "reports/route_764_accuracy_predictions.csv"

print("\nLoading GPS observations and schedule estimates...")

gps = pd.read_csv(GPS_FILE)
schedule = pd.read_csv(SCHEDULE_FILE)

# Standardise stop IDs so both files can be matched.
for df, columns in [
    (gps, ["from_stop_id", "to_stop_id"]),
    (schedule, ["from_stop_id", "to_stop_id"])
]:
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

gps["travel_seconds"] = pd.to_numeric(
    gps["travel_seconds"], errors="coerce"
)

schedule["scheduled_seconds"] = pd.to_numeric(
    schedule["travel_time_seconds"], errors="coerce"
)

schedule = schedule.dropna(
    subset=["from_stop_id", "to_stop_id", "scheduled_seconds"]
)

gps = gps.dropna(
    subset=[
        "trip_id", "from_stop_id",
        "to_stop_id", "travel_seconds"
    ]
)

# One schedule value for each stop pair.
schedule = schedule.drop_duplicates(
    subset=["from_stop_id", "to_stop_id"]
)

# Attach the schedule baseline to every GPS observation.
data = gps.merge(
    schedule[
        ["from_stop_id", "to_stop_id", "scheduled_seconds"]
    ],
    on=["from_stop_id", "to_stop_id"],
    how="inner"
)

print("GPS observations:", len(gps))
print("Matched evaluation observations:", len(data))
print("Unique GPS trips:", data["trip_id"].nunique())
print("Unique stop pairs:", data[
    ["from_stop_id", "to_stop_id"]
].drop_duplicates().shape[0])

if data.empty:
    raise ValueError("No matching GPS and schedule observations found.")

# Leave-one-trip-out evaluation.
# The held-out trip is excluded entirely from its GPS training median.
predictions = []

for trip_id in data["trip_id"].unique():

    test_rows = data[data["trip_id"] == trip_id]
    train_rows = data[data["trip_id"] != trip_id]

    for _, row in test_rows.iterrows():

        pair_train = train_rows[
            (train_rows["from_stop_id"] == row["from_stop_id"]) &
            (train_rows["to_stop_id"] == row["to_stop_id"])
        ]

        actual = float(row["travel_seconds"])
        scheduled = float(row["scheduled_seconds"])

        if len(pair_train) > 0:
            gps_median = float(pair_train["travel_seconds"].median())

            # 50% GPS median + 50% scheduled time.
            predicted = (gps_median + scheduled) / 2
            source = "GPS + Schedule"
            training_observations = len(pair_train)
        else:
            predicted = scheduled
            source = "Schedule fallback"
            training_observations = 0

        predictions.append({
            "trip_id": trip_id,
            "from_stop_id": int(row["from_stop_id"]),
            "to_stop_id": int(row["to_stop_id"]),
            "actual_seconds": actual,
            "schedule_prediction_seconds": scheduled,
            "gps_schedule_prediction_seconds": predicted,
            "prediction_source": source,
            "training_observations": training_observations
        })

results = pd.DataFrame(predictions)

def calculate_metrics(actual, predicted):
    errors = np.asarray(predicted) - np.asarray(actual)
    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors ** 2))
    return mae, rmse

def show_metrics(name, subset):
    mae, rmse = calculate_metrics(
        subset["actual_seconds"],
        subset[name]
    )
    print(f"MAE:  {mae:.2f} seconds ({mae / 60:.2f} minutes)")
    print(f"RMSE: {rmse:.2f} seconds ({rmse / 60:.2f} minutes)")

print("\n" + "=" * 65)
print("ROUTE 764DOWN - PREDICTION ACCURACY")
print("LEAVE-ONE-TRIP-OUT EVALUATION")
print("=" * 65)

print("\nTOTAL EVALUATION OBSERVATIONS:", len(results))

gps_test = results[
    results["prediction_source"] == "GPS + Schedule"
]

fallback_test = results[
    results["prediction_source"] == "Schedule fallback"
]

print("GPS-informed predictions:", len(gps_test))
print("Schedule fallback predictions:", len(fallback_test))

print("\n1. SCHEDULE-ONLY BASELINE (ALL OBSERVATIONS)")
show_metrics("schedule_prediction_seconds", results)

print("\n2. GPS + SCHEDULE MODEL (GPS-COVERED OBSERVATIONS)")
if len(gps_test) > 0:
    show_metrics("gps_schedule_prediction_seconds", gps_test)

    print("\n3. SCHEDULE BASELINE ON THE SAME GPS-COVERED OBSERVATIONS")
    show_metrics("schedule_prediction_seconds", gps_test)

    baseline_mae, _ = calculate_metrics(
        gps_test["actual_seconds"],
        gps_test["schedule_prediction_seconds"]
    )
    model_mae, _ = calculate_metrics(
        gps_test["actual_seconds"],
        gps_test["gps_schedule_prediction_seconds"]
    )

    improvement = baseline_mae - model_mae
    percentage = (
        improvement / baseline_mae * 100
        if baseline_mae else 0
    )

    print(f"\nMAE improvement: {improvement:.2f} seconds")
    print(f"MAE improvement percentage: {percentage:.2f}%")
else:
    print("No GPS-covered test observations available.")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
results.to_csv(OUTPUT_FILE, index=False)

print("\nPrediction-level results saved to:")
print(OUTPUT_FILE)

print("\nEvaluation completed.")
