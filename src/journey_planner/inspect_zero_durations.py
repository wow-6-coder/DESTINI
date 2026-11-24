import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

FILE = PROJECT / "data" / "processed" / "bus_connections.csv"

df = pd.read_csv(FILE)

zero = df[df["travel_time_seconds"] == 0]

print("Total zero-duration connections:", len(zero))

print("\nFirst 30 zero-duration records:")
print(zero.head(30).to_string(index=False))

print("\nUnique trips affected:", zero["trip_id"].nunique())

print("\nZero-duration connections by stop:")
print(zero["from_stop"].value_counts().head(10))
print("\n========== ZERO-DURATION CLASSIFICATION ==========")

print(
    "Same stop:",
    (zero["from_stop"] == zero["to_stop"]).sum()
)

print(
    "Different stops:",
    (zero["from_stop"] != zero["to_stop"]).sum()
)

print(
    "Same stop percentage:",
    round(
        (zero["from_stop"] == zero["to_stop"]).mean() * 100,
        2
    ),
    "%"
)

print("==================================================")