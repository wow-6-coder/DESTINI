
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
FILE = PROJECT / "data" / "processed" / "bus_connections.csv"

df = pd.read_csv(FILE)

print("\n========== CONNECTION QUALITY AUDIT ==========")

print("Total connections:", len(df))
print("Missing values:", df.isna().sum().sum())

print("\nTravel time statistics (minutes):")
print((df["travel_time_seconds"] / 60).describe())

print("\nInvalid or unusual durations:")
print("Negative:", (df["travel_time_seconds"] < 0).sum())
print("Zero:", (df["travel_time_seconds"] == 0).sum())
print("Above 2 hours:", (df["travel_time_seconds"] > 7200).sum())

print("\nSample connections:")
print(df.head(10).to_string(index=False))

print("==============================================")
