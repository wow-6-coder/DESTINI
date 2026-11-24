import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT / "data" / "processed" / "bus_connections.csv"
OUTPUT_FILE = PROJECT / "data" / "processed" / "bus_connections_clean.csv"

print("Loading connections...")

df = pd.read_csv(INPUT_FILE)

original_count = len(df)

# Remove connections that start and end at the same stop
cleaned = df[df["from_stop"] != df["to_stop"]].copy()

removed_count = original_count - len(cleaned)

cleaned.to_csv(OUTPUT_FILE, index=False)

print("\n========== CLEANING COMPLETE ==========")
print("Original connections:", original_count)
print("Removed self-loops:", removed_count)
print("Remaining connections:", len(cleaned))
print("Output file:", OUTPUT_FILE)
print("=======================================")