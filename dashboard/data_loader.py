import pandas as pd

def load_data():
    df = pd.read_csv("processed_data/merged_field_production.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df
