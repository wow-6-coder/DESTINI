from pathlib import Path
import pandas as pd
import numpy as np

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

schedule = schedule.dropna(
    subset=["from_stop_id", "to_stop_id", "scheduled_seconds"]
).drop_duplicates(["from_stop_id", "to_stop_id"])

data = gps.merge(
    schedule[["from_stop_id", "to_stop_id", "scheduled_seconds"]],
    on=["from_stop_id", "to_stop_id"],
    how="inner"
).dropna(subset=["trip_id", "travel_seconds"])

weights = [0, 0.25, 0.50, 0.75, 1.0]
predictions = []

print("Running leave-one-trip-out weight experiments...")

for trip_id in data["trip_id"].unique():

    test = data[data["trip_id"] == trip_id]
    train = data[data["trip_id"] != trip_id]

    for _, row in test.iterrows():

        pair_train = train[
            (train["from_stop_id"] == row["from_stop_id"]) &
            (train["to_stop_id"] == row["to_stop_id"])
        ]

        if pair_train.empty:
            continue

        gps_median = pair_train["travel_seconds"].median()
        scheduled = row["scheduled_seconds"]
        actual = row["travel_seconds"]

        for weight in weights:
            prediction = (
                weight * gps_median +
                (1 - weight) * scheduled
            )

            predictions.append({
                "trip_id": trip_id,
                "gps_weight": weight,
                "actual": actual,
                "prediction": prediction
            })

results = pd.DataFrame(predictions)

summary = []

for weight, group in results.groupby("gps_weight"):

    errors = group["prediction"] - group["actual"]

    summary.append({
        "GPS weight": f"{weight * 100:.0f}%",
        "Schedule weight": f"{(1-weight) * 100:.0f}%",
        "Observations": len(group),
        "MAE seconds": np.mean(np.abs(errors)),
        "RMSE seconds": np.sqrt(np.mean(errors ** 2))
    })

summary = pd.DataFrame(summary).sort_values("MAE seconds")

output = BASE / "reports/gps_blending_experiments.csv"
summary.to_csv(output, index=False)

print("\n" + "=" * 65)
print("GPS BLENDING WEIGHT COMPARISON")
print("=" * 65)
print(summary.round(2).to_string(index=False))

print("\nBest weight by MAE:")
print(summary.iloc[0].to_string())

print("\nSaved:", output)
