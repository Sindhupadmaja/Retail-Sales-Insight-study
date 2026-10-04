import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def con():
    """A tiny in-memory copy of the Olist schema with hand-checkable values."""
    c = duckdb.connect()
    tables = {
        "orders": pd.DataFrame({
            "order_id": ["o1", "o2", "o3", "o4"],
            "customer_id": ["c1", "c2", "c3", "c4"],
            "order_status": ["delivered", "delivered", "canceled", "delivered"],
            "order_purchase_timestamp": ["2017-01-05 10:00:00", "2017-01-20 12:00:00",
                                         "2017-02-01 09:00:00", "2018-01-10 15:00:00"],
            "order_delivered_customer_date": ["2017-01-10 10:00:00", "2017-02-15 12:00:00",
                                              None, "2018-01-15 10:00:00"],
            "order_estimated_delivery_date": ["2017-01-20 00:00:00", "2017-02-01 00:00:00",
                                              "2017-02-20 00:00:00", "2018-01-30 00:00:00"],
        }),
        "customers": pd.DataFrame({"customer_id": ["c1", "c2", "c3", "c4"],
                                   "customer_unique_id": ["u1", "u2", "u3", "u1"],
                                   "customer_state": ["SP", "RJ", "SP", "SP"]}),
        "order_items": pd.DataFrame({"order_id": ["o1", "o1", "o2", "o3", "o4"],
                                     "product_id": ["p1", "p2", "p1", "p1", "p2"],
                                     "price": [50.0, 30.0, 100.0, 999.0, 40.0],
                                     "freight_value": [10.0, 5.0, 20.0, 1.0, 8.0]}),
        "order_reviews": pd.DataFrame({"order_id": ["o1", "o2", "o2", "o4"],
                                       "review_score": [5, 3, 1, 4],
                                       "review_answer_timestamp": ["2017-01-11", "2017-02-16",
                                                                   "2017-02-20", "2018-01-16"]}),
        "products": pd.DataFrame({"product_id": ["p1", "p2"],
                                  "product_category_name": ["beleza_saude", "esporte_lazer"]}),
        "category_translation": pd.DataFrame({
            "product_category_name": ["beleza_saude", "esporte_lazer"],
            "product_category_name_english": ["health_beauty", "sports_leisure"]}),
    }
    for name, df in tables.items():
        c.register(f"{name}_df", df)
        c.execute(f"CREATE TABLE {name} AS SELECT * FROM {name}_df")
    c.execute((ROOT / "sql/01_model.sql").read_text())
    return c
