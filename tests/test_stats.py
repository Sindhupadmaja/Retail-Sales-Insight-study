import pandas as pd

from src import stats


def test_late_vs_on_time_difference():
    df = pd.DataFrame({"is_late": [1, 1, 0, 0, 0, 0], "review_score": [1, 3, 5, 5, 4, 4],
                       "customer_state": ["SP"] * 6})
    r = stats.late_vs_on_time(df, n_boot=200)
    assert r["mean_difference"] == 2 - 4.5
    assert r["ci_low"] <= r["mean_difference"] <= r["ci_high"]


def test_stratified_difference_weights_groups():
    df = pd.DataFrame({
        "customer_state": ["A"] * 4 + ["B"] * 4,
        "is_late": [1, 1, 0, 0] * 2,
        "review_score": [2, 2, 4, 4, 3, 3, 4, 4],
    })
    gap, table = stats.stratified_difference(df, min_orders=1)
    assert gap == (-2 + -1) / 2
    assert len(table) == 2
