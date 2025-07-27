import pandas as pd
import os

# Define paths
PROC_DIR = "processed_data"
OUT_FILE = "merged_field_production.csv"

# Load data
net = pd.read_csv(os.path.join(PROC_DIR, "production_clean.csv"))
gross = pd.read_csv(os.path.join(PROC_DIR, "production_gross_clean.csv"))
locations = pd.read_csv(os.path.join(PROC_DIR, "field_locations.csv"))

# Normalise field names
net["field"] = net["field"].str.strip().str.upper()
gross["field"] = gross["field"].str.strip().str.upper()
locations["fldName"] = locations["fldName"].str.strip().str.upper()

# Merge net and gross
merged = pd.merge(
    net,
    gross,
    on=["field", "date", "product", "unit"],
    how="outer",
    suffixes=("_net", "_gross")
)
merged["volume_net"] = merged["volume_net"].fillna(0)
merged["volume_gross"] = merged["volume_gross"].fillna(0)

# Merge with location info
merged = pd.merge(
    merged,
    locations,
    left_on="field",
    right_on="fldName",
    how="left"
).drop(columns=["fldName"])

# Reorder columns
merged = merged[[
    "field", "date", "product",
    "volume_net", "volume_gross", "unit",
    "avg_lat", "avg_lon", "fldMainArea", "status", "hc_type"
]]

# Save output
merged.to_csv(os.path.join(PROC_DIR, OUT_FILE), index=False)
print(f"✅ Saved merged dataset to {PROC_DIR}/{OUT_FILE}")
