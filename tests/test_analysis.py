import pandas as pd
from src.analysis import summarize

def test_revenue_summary():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2025-01-01"]),
        "store_id": ["S01"], "category": ["Home"], "product_id": ["P1"],
        "units": [4], "unit_price": [10]
    })
    df["revenue"] = df["units"] * df["unit_price"]
    monthly, products, categories = summarize(df)
    assert products.iloc[0]["revenue"] == 40
