
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
FILE = PROJECT / "data" / "processed" / "gps_stop_matches_764.csv"

df = pd.read_csv(FILE)

print("\n========== COLUMNS ==========")
print(df.columns.tolist())

print("\n========== DATA TYPES ==========")
print(df.dtypes)

print("\n========== FIRST 10 MATCHED RECORDS ==========")
print(df.head(10).to_string(index=False))

print("\n========== SAMPLE TRIP ==========")
trip = df["trip_id"].dropna().iloc[0]
sample = df[df["trip_id"] == trip].head(20)
print(sample.to_string(index=False))

print("\nSample trip ID:", trip)
