
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

INPUT = (
    PROJECT / "data" / "processed"
    / "gps_vs_schedule_comparison.csv"
)

OUTPUT = (
    PROJECT / "data" / "processed"
    / "gps_adjusted_travel_times.csv"
)

df = pd.read_csv(INPUT)

# Blend GPS and scheduled travel times
df["adjusted_minutes"] = (
    0.5 * df["gps_median_minutes"]
    + 0.5 * df["scheduled_median_minutes"]
).round(2)

df["gps_contribution"] = "50%"
df["schedule_contribution"] = "50%"

df.to_csv(OUTPUT, index=False)

print("\n========== ADJUSTED TRAVEL TIME REPORT ==========")
print("Stop pairs:", len(df))

print("\nSample adjusted estimates:")
print(
    df[
        [
            "from_stop_name",
            "to_stop_name",
            "observations",
            "gps_median_minutes",
            "scheduled_median_minutes",
            "adjusted_minutes"
        ]
    ].head(15).to_string(index=False)
)

print("\nOutput:", OUTPUT)
