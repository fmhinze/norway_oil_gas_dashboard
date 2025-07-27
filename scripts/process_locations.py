# scripts/process_locations.py
import pandas as pd
import os

# Paths
RAW_DIR = "raw_data"
PROC_DIR = "processed_data"

# Load raw data
fields = pd.read_csv(os.path.join(RAW_DIR, "field.csv"))
wells = pd.read_csv(os.path.join(RAW_DIR, "wellbore_all_long.csv"))

# Drop wells without coordinates
wells = wells.dropna(subset=["wlbNsDecDeg", "wlbEwDecDeg"])

# Merge wells with field metadata
merged = wells.merge(fields, on="fldNpdidField", suffixes=("_well", "_field"))

# Group by field to compute average location
field_coords = merged.groupby("fldName").agg({
    "wlbNsDecDeg": "mean",
    "wlbEwDecDeg": "mean",
    "fldMainArea": "first",
    "fldCurrentActivitySatus": "first",
    "fldHcType": "first"
}).reset_index()

# Rename columns
field_coords.columns = ["fldName", "avg_lat", "avg_lon", "fldMainArea", "status", "hc_type"]

# Save to processed_data
field_coords.to_csv(os.path.join(PROC_DIR, "field_locations.csv"), index=False)

print("Field locations saved to 'processed_data/field_locations.csv'")
