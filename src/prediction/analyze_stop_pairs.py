from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parents[2]

PREDICTION_FILE = BASE / "reports/route_764_accuracy_predictions.csv"
GPS_FILE = BASE / "data/processed/gps_travel_times_764.csv"

OUTPUT_FILE = BASE / "reports/stop_pair_accuracy_analysis.csv"

print("\nLoading prediction results...")

df = pd.read_csv(PREDICTION_FILE)
gps = pd.read_csv(GPS_FILE)

# Get stop names for each stop ID.
names = gps[
    ["from_stop_id", "from_stop_name",
     "to_stop_id", "to_stop_name"]
].drop_duplicates()

from_names = names[
    ["from_stop_id", "from_stop_name"]
].drop_duplicates("from_stop_id")

to_names = names[
    ["to_stop_id", "to_stop_name"]
].drop_duplicates("to_stop_id")

df = df.merge(from_names, on="from_stop_id", how="left")
df = df.merge(to_names, on="to_stop_id", how="left")

# Only compare GPS-informed predictions against schedule
# for observations with an available GPS-informed estimate.
df = df[
    df["prediction_source"] == "GPS + Schedule"
].copy()

df["schedule_error"] = (
    df["schedule_prediction_seconds"] - df["actual_seconds"]
)

df["model_error"] = (
    df["gps_schedule_prediction_seconds"] - df["actual_seconds"]
)

df["schedule_absolute_error"] = df["schedule_error"].abs()
df["model_absolute_error"] = df["model_error"].abs()

df["schedule_squared_error"] = df["schedule_error"] ** 2
df["model_squared_error"] = df["model_error"] ** 2

grouped = df.groupby(
    ["from_stop_id", "to_stop_id"],
    dropna=False
).agg(
    observations=("actual_seconds", "size"),
    from_stop=("from_stop_name", "first"),
    to_stop=("to_stop_name", "first"),
    actual_mean_seconds=("actual_seconds", "mean"),
    schedule_mae=("schedule_absolute_error", "mean"),
    model_mae=("model_absolute_error", "mean"),
    schedule_mse=("schedule_squared_error", "mean"),
    model_mse=("model_squared_error", "mean")
).reset_index()

grouped["schedule_rmse"] = np.sqrt(grouped["schedule_mse"])
grouped["model_rmse"] = np.sqrt(grouped["model_mse"])

grouped["mae_improvement_seconds"] = (
    grouped["schedule_mae"] - grouped["model_mae"]
)

grouped["rmse_improvement_seconds"] = (
    grouped["schedule_rmse"] - grouped["model_rmse"]
)

grouped["mae_improvement_percent"] = np.where(
    grouped["schedule_mae"] > 0,
    grouped["mae_improvement_seconds"] /
    grouped["schedule_mae"] * 100,
    np.nan
)

grouped["result"] = np.where(
    grouped["mae_improvement_seconds"] > 0,
    "GPS improved",
    np.where(
        grouped["mae_improvement_seconds"] < 0,
        "GPS worsened",
        "No change"
    )
)

grouped = grouped.sort_values(
    "mae_improvement_seconds",
    ascending=False
)

grouped.to_csv(OUTPUT_FILE, index=False)

print("\n" + "=" * 75)
print("STOP-PAIR PREDICTION ACCURACY ANALYSIS")
print("=" * 75)

print("\nTOTAL STOP PAIRS:", len(grouped))

print("\nRESULT CATEGORY COUNTS:")
print(grouped["result"].value_counts().to_string())

print("\nTOP 10 PAIRS WHERE GPS IMPROVED MAE:")
print(
    grouped.head(10)[[
        "from_stop_id", "from_stop",
        "to_stop_id", "to_stop",
        "observations",
        "schedule_mae", "model_mae",
        "mae_improvement_seconds",
        "mae_improvement_percent"
    ]].round(2).to_string(index=False)
)

print("\nTOP 10 PAIRS WHERE GPS WORSENED MAE:")
print(
    grouped.tail(10).sort_values(
        "mae_improvement_seconds"
    )[[
        "from_stop_id", "from_stop",
        "to_stop_id", "to_stop",
        "observations",
        "schedule_mae", "model_mae",
        "mae_improvement_seconds",
        "mae_improvement_percent"
    ]].round(2).to_string(index=False)
)

print("\nPAIRS WITH AT LEAST 5 TEST OBSERVATIONS:")
reliable = grouped[grouped["observations"] >= 5]

print("Number of pairs:", len(reliable))

print("\nGPS IMPROVED:",
      (reliable["result"] == "GPS improved").sum())

print("GPS WORSENED:",
      (reliable["result"] == "GPS worsened").sum())

print("\nREPORT SAVED:")
print(OUTPUT_FILE)

print("\nAnalysis completed.")
