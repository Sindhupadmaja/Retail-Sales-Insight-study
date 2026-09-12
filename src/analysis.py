import pandas as pd

def load_sales(path):
    df = pd.read_csv(path, parse_dates=["date"])
    required = {"date","store_id","category","product_id","units","unit_price"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    df["revenue"] = df["units"] * df["unit_price"]
    return df

def summarize(df):
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    monthly = df.groupby("month", as_index=False)["revenue"].sum()
    products = df.groupby("product_id", as_index=False).agg(
        units=("units","sum"), revenue=("revenue","sum")
    ).sort_values("revenue", ascending=False)
    categories = df.groupby("category", as_index=False)["revenue"].sum()
    return monthly, products, categories
