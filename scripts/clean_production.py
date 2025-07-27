import pandas as pd
import os

RAW_DIR = "raw_data"
PROC_DIR = "processed_data"

# Load raw production file
df = pd.read_csv(os.path.join(RAW_DIR, "field_production_monthly.csv"))

# Rename for clarity
df = df.rename(columns={
    "prfInformationCarrier": "field",
    "prfYear": "year",
    "prfMonth": "month",
    "prfPrdOilNetMillSm3": "oil_mill_sm3",
    "prfPrdGasNetBillSm3": "gas_bill_sm3",
    "prfPrdNGLNetMillSm3": "ngl_mill_sm3",
    "prfPrdCondensateNetMillSm3": "cond_mill_sm3",
})

# Combine year and month into a date
df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))

# Select relevant columns
df = df[["field", "date", "oil_mill_sm3", "gas_bill_sm3", "ngl_mill_sm3", "cond_mill_sm3"]]

# Melt to long format
df_long = df.melt(
    id_vars=["field", "date"],
    var_name="product",
    value_name="volume"
)

# Clean product names
product_map = {
    "oil_mill_sm3": ("Oil", "mill_sm3"),
    "gas_bill_sm3": ("Gas", "bill_sm3"),
    "ngl_mill_sm3": ("NGL", "mill_sm3"),
    "cond_mill_sm3": ("Condensate", "mill_sm3"),
}

df_long["product"] = df_long["product"].map(lambda x: product_map[x][0])
df_long["unit"] = df_long["product"].map(lambda x: {
    "Oil": "mill_sm3",
    "Gas": "bill_sm3",
    "NGL": "mill_sm3",
    "Condensate": "mill_sm3"
}[x])

# Optional: remove zero rows to slim the file
df_long = df_long[df_long["volume"] > 0]

# Save cleaned version
df_long.to_csv(os.path.join(PROC_DIR, "production_clean.csv"), index=False)

print("✅ Cleaned production saved to 'processed_data/production_clean.csv'")
