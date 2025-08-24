import pandas as pd
import os

RAW_DIR = "raw_data"
PROC_DIR = "processed_data"

# Load raw production file
df = pd.read_csv(os.path.join(RAW_DIR, "field_reserves.csv"))

#df = df[["fldName", "fldRecoverableOil", "fldRecoverableGas", "fldRecoverableNGL" , "fldRecoverableCondensate"]]

# Save cleaned version
df.to_csv(os.path.join(PROC_DIR, "field_reserves.csv"), index=False)

print("✅ Reserves saved to 'processed_data/field_reserves.csv'")
