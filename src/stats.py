"""Statistical checks on the late-delivery effect on review scores."""
import numpy as np
import pandas as pd
from scipy import stats


def late_vs_on_time(orders, n_boot=2000, seed=42):
    """Difference in mean review score (late - on time) with a bootstrap CI and Mann-Whitney test."""
    d = orders.dropna(subset=["is_late", "review_score"])
    late = d.loc[d["is_late"] == 1, "review_score"].to_numpy(float)
    ontime = d.loc[d["is_late"] == 0, "review_score"].to_numpy(float)
    rng = np.random.default_rng(seed)
    boots = np.array([rng.choice(late, late.size).mean() - rng.choice(ontime, ontime.size).mean()
                      for _ in range(n_boot)])
    return {
        "late_orders": int(late.size), "on_time_orders": int(ontime.size),
        "mean_difference": float(late.mean() - ontime.mean()),
        "ci_low": float(np.quantile(boots, 0.025)), "ci_high": float(np.quantile(boots, 0.975)),
        "mann_whitney_p": float(stats.mannwhitneyu(late, ontime).pvalue),
    }


def stratified_difference(orders, by="customer_state", min_orders=100):
    """Late vs on-time review gap computed within each group, then weighted by group size.

    Late deliveries are more common in some states, and those states may review differently
    for other reasons. Comparing within states removes that geographic confounding."""
    d = orders.dropna(subset=["is_late", "review_score"])
    rows = []
    for g, sub in d.groupby(by):
        late, ontime = sub[sub["is_late"] == 1], sub[sub["is_late"] == 0]
        if len(late) >= min_orders and len(ontime) >= min_orders:
            rows.append({"group": g, "n": len(sub),
                         "gap": late["review_score"].mean() - ontime["review_score"].mean()})
    r = pd.DataFrame(rows)
    return float(np.average(r["gap"], weights=r["n"])), r
