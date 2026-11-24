from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]

gps = pd.read_csv(BASE / "data/processed/gps_travel_times_764.csv")
schedule = pd.read_csv(
    BASE / "data/processed/route_764_integrated_estimates.csv"
)

for df in [gps, schedule]:
    for col in ["from_stop_id", "to_stop_id"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

gps["travel_seconds"] = pd.to_numeric(
    gps["travel_seconds"], errors="coerce"
)
schedule["scheduled_seconds"] = pd.to_numeric(
    schedule["travel_time_seconds"], errors="coerce"
)

gps = gps.dropna(
    subset=["trip_id", "from_stop_id", "to_stop_id", "travel_seconds"]
)

schedule = schedule.dropna(
    subset=["from_stop_id", "to_stop_id", "scheduled_seconds"]
).drop_duplicates(["from_stop_id", "to_stop_id"])

data = gps.merge(
    schedule[["from_stop_id", "to_stop_id", "scheduled_seconds"]],
    on=["from_stop_id", "to_stop_id"],
    how="inner"
)

# Split by complete trip IDs, never by individual observations.
trip_ids = np.asarray(
    data["trip_id"].unique().tolist(),
    dtype=object
)

rng = np.random.default_rng(42)
rng.shuffle(trip_ids)

n = len(trip_ids)
train_end = int(n * 0.60)
validation_end = int(n * 0.80)

train_ids = trip_ids[:train_end]
validation_ids = trip_ids[train_end:validation_end]
test_ids = trip_ids[validation_end:]

train = data[data["trip_id"].isin(train_ids)]
validation = data[data["trip_id"].isin(validation_ids)]
test = data[data["trip_id"].isin(test_ids)]

print("TRIP SPLIT")
print("Training trips:", len(train_ids))
print("Validation trips:", len(validation_ids))
print("Test trips:", len(test_ids))
print("Training observations:", len(train))
print("Validation observations:", len(validation))
print("Test observations:", len(test))

# Calculate GPS medians using training trips only.
medians = train.groupby(
    ["from_stop_id", "to_stop_id"]
)["travel_seconds"].median().rename("gps_median").reset_index()

weights = [0, 0.25, 0.50, 0.75, 1.0]

def predict(frame):
    result = frame.merge(
        medians,
        on=["from_stop_id", "to_stop_id"],
        how="left"
    )
    return result

validation = predict(validation)
test = predict(test)

def evaluate(frame, weight):
    gps_available = frame["gps_median"].notna()

    prediction = np.where(
        gps_available,
        weight * frame["gps_median"].fillna(0)
        + (1 - weight) * frame["scheduled_seconds"],
        frame["scheduled_seconds"]
    )

    errors = prediction - frame["travel_seconds"]

    return {
        "weight": weight,
        "observations": len(frame),
        "gps_covered": int(gps_available.sum()),
        "fallback": int((~gps_available).sum()),
        "MAE": np.mean(np.abs(errors)),
        "RMSE": np.sqrt(np.mean(errors ** 2))
    }

# Select weight on validation data only.
validation_results = pd.DataFrame([
    evaluate(validation, w) for w in weights
])

best_row = validation_results.sort_values(
    "MAE"
).iloc[0]

best_weight = float(best_row["weight"])

# Evaluate the selected weight on untouched test trips.
test_results = pd.DataFrame([
    evaluate(test, w) for w in weights
])

chosen = test_results[test_results["weight"] == best_weight].iloc[0]
baseline = test_results[test_results["weight"] == 0].iloc[0]

print("\n" + "=" * 65)
print("VALIDATION RESULTS")
print("=" * 65)
print(validation_results.round(2).to_string(index=False))

print("\nSelected GPS weight:", f"{best_weight * 100:.0f}%")

print("\n" + "=" * 65)
print("UNSEEN TEST TRIP RESULTS")
print("=" * 65)
print(test_results.round(2).to_string(index=False))

print("\nSELECTED MODEL VS SCHEDULE BASELINE")
print("Selected model MAE:", round(chosen["MAE"], 2), "seconds")
print("Schedule MAE:", round(baseline["MAE"], 2), "seconds")
print("Selected model RMSE:", round(chosen["RMSE"], 2), "seconds")
print("Schedule RMSE:", round(baseline["RMSE"], 2), "seconds")

if baseline["MAE"] > 0:
    improvement = (
        baseline["MAE"] - chosen["MAE"]
    ) / baseline["MAE"] * 100
    print("Test MAE improvement:", round(improvement, 2), "%")

print("\nGPS coverage on test trips:",
      f'{chosen["gps_covered"]}/{chosen["observations"]}')

output = BASE / "reports/independent_trip_holdout_results.csv"
test_results.to_csv(output, index=False)

validation_results.to_csv(
    BASE / "reports/validation_weight_results.csv",
    index=False
)

print("\nReports saved:")
print(output)
print(BASE / "reports/validation_weight_results.csv")
