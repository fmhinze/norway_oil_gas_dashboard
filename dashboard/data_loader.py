import pandas as pd

def load_data():
    df = pd.read_csv("processed_data/merged_field_production.csv")
    df["date"] = pd.to_datetime(df["date"])
    
    df_reserves = pd.read_csv("processed_data/field_reserves.csv")
    return df, df_reserves
