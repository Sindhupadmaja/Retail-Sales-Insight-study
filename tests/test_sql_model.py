from src import config as cfg
from src import db


def test_canceled_orders_excluded_and_revenue_summed(con):
    f = con.execute("SELECT order_id, product_revenue, items FROM fact_orders ORDER BY order_id").df()
    assert list(f["order_id"]) == ["o1", "o2", "o4"]          # o3 was canceled
    assert f.loc[f.order_id == "o1", "product_revenue"].iloc[0] == 80
    assert f.loc[f.order_id == "o1", "items"].iloc[0] == 2


def test_late_flag_and_latest_review(con):
    f = con.execute("SELECT order_id, is_late, review_score FROM fact_orders ORDER BY order_id").df().set_index("order_id")
    assert f.loc["o2", "is_late"] == 1 and f.loc["o1", "is_late"] == 0
    assert f.loc["o2", "review_score"] == 1                   # most recent of two reviews


def test_category_translation(con):
    cats = set(con.execute("SELECT DISTINCT category FROM fact_items").df()["category"])
    assert cats == {"health_beauty", "sports_leisure"}


def test_named_queries_run_and_repeat_rate(con):
    q = db.load_queries(cfg.SQL / "02_kpis.sql")
    assert {"monthly_kpis", "repeat_customers", "delivery_vs_reviews"} <= set(q)
    rep = db.query(con, q["repeat_customers"])
    assert rep["customers"].iloc[0] == 2                      # u1 ordered twice, u2 once
    assert rep["repeat_rate"].iloc[0] == 0.5
    monthly = db.query(con, q["monthly_kpis"], {"start": "2017-01-01", "end": "2018-12-01"})
    assert monthly["orders"].sum() == 3
