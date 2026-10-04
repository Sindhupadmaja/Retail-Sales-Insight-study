"""End-to-end run: CSVs -> DuckDB SQL model -> KPI queries -> statistics -> charts, dashboard, summary.

Run from the repository root:  python -m src.pipeline
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src import config as cfg
from src import dashboard, db, stats


def run_queries(con):
    queries = db.load_queries(cfg.SQL / "02_kpis.sql")
    params = {"start": cfg.START_MONTH, "end": cfg.END_MONTH}
    return {name: db.query(con, sql, params if "$start" in sql else None)
            for name, sql in queries.items()}


def plot_monthly(m, path):
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.bar(m["order_month"], m["revenue"] / 1e3, width=20)
    ax.set_ylabel("Revenue (R$ thousands)")
    ax2 = ax.twinx()
    ax2.plot(m["order_month"], m["late_rate"] * 100, color="tab:red", marker="o")
    ax2.set_ylabel("Late deliveries (%)", color="tab:red")
    ax.set_title("Monthly revenue vs late-delivery rate")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_delivery(curve, path):
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.plot(curve["days_vs_estimate"], curve["avg_review"], marker="o")
    ax.axvline(0, color="grey", linestyle="--")
    ax.set_xlabel("Days delivered after the promised date (negative = early; capped at ±20)")
    ax.set_ylabel("Average review score")
    ax.set_title("Reviews collapse once an order misses its promised delivery date")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_pareto(cat, path, n=25):
    c = cat.head(n)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.bar(c["category"], c["revenue_share"] * 100)
    ax.set_ylabel("Share of revenue (%)")
    ax.tick_params(axis="x", rotation=75, labelsize=8)
    ax2 = ax.twinx()
    ax2.plot(c["category"], c["cumulative_share"] * 100, color="tab:red", marker=".")
    ax2.axhline(80, color="tab:red", linestyle=":")
    ax2.set_ylabel("Cumulative share (%)", color="tab:red")
    ax.set_title(f"Category revenue concentration (top {n} of {len(cat)})")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def summary_markdown(k):
    return f"""# Executive summary

## Growth
Revenue grew **{k['yoy_revenue_growth']:.0%}** in January–August 2018 versus the same months of 2017,
driven almost entirely by order volume (+{k['yoy_order_growth']:.0%}) rather than basket size.
The single biggest day was Black Friday, {k['peak_day']}, with {k['peak_day_orders']:,} orders,
{k['peak_multiple']:.1f}× the average day in November 2017.

## Customer experience is the main risk
{k['late_share']:.1%} of delivered orders arrived after the promised date. Those orders averaged
**{k['late_review']:.2f} stars versus {k['ontime_review']:.2f}** for on-time orders, and
{k['late_bad']:.0%} of them received a 1–2 star review (vs {k['ontime_bad']:.0%}). The gap holds
within states ({k['stratified_gap']:+.2f} stars after controlling for geography), so it is not explained
by regional differences. Late rates are highest in {k['worst_states']}.

## Retention is very low
Only **{k['repeat_rate']:.1%}** of {k['customers']:,} customers ordered more than once, so growth
depends on acquiring new customers.

## Concentration
The top {k['n_cats_50']} of {k['n_cats']} categories generate half of revenue, led by
{k['top_categories']}.

## Recommendations
1. Set delivery promises from actual carrier performance in high-late-rate states, and alert
   customers proactively when an order is at risk of missing its date.
2. Launch a second-purchase program (for example, post-delivery offers to customers whose order
   arrived on time and was rated 4–5 stars), since repeat buying is almost absent.
3. Plan carrier capacity ahead of Black Friday: in November 2017 the late rate rose to
   {k['nov_late_rate']:.0%} (from {k['pre_nov_late_rate']:.0%} on average in January–October) and the
   average review fell to {k['nov_review']:.2f}, the lowest of the year.
"""


def main():
    cfg.FIGURES.mkdir(parents=True, exist_ok=True)
    con = db.connect(cfg.RAW, cfg.TABLES)
    db.run_script(con, cfg.SQL / "01_model.sql")
    r = run_queries(con)
    orders = db.query(con, "SELECT customer_state, is_late, review_score FROM fact_orders")

    test = stats.late_vs_on_time(orders, cfg.N_BOOTSTRAP, cfg.RANDOM_STATE)
    strat_gap, strat = stats.stratified_difference(orders)

    for name, df in r.items():
        df.to_csv(cfg.REPORTS / f"{name}.csv", index=False)
    plot_monthly(r["monthly_kpis"], cfg.FIGURES / "monthly_revenue_late_rate.png")
    plot_delivery(r["review_by_days_late"], cfg.FIGURES / "review_vs_days_late.png")
    plot_pareto(r["category_performance"], cfg.FIGURES / "category_pareto.png")

    dv = r["delivery_vs_reviews"].set_index("delivery")
    cat = r["category_performance"]
    states = r["state_performance"]
    big_states = states[states["orders"] >= 1000].sort_values("late_rate", ascending=False)
    peak = r["peak_days"].iloc[0]
    nov = r["monthly_kpis"]
    nov_orders = nov.loc[nov["order_month"].astype(str).str.startswith("2017-11"), "orders"].iloc[0]
    months = nov["order_month"].astype(str)
    is_nov = months.str.startswith("2017-11")
    pre_nov = months.between("2017-01", "2017-10-31")
    k = {
        "nov_late_rate": float(nov.loc[is_nov, "late_rate"].iloc[0]),
        "pre_nov_late_rate": float(nov.loc[pre_nov, "late_rate"].mean()),
        "nov_review": float(nov.loc[is_nov, "avg_review"].iloc[0]),
        "yoy_revenue_growth": float(r["yoy_growth"]["revenue_growth"].iloc[0]),
        "yoy_order_growth": float(r["yoy_growth"]["order_growth"].iloc[0]),
        "peak_day": str(peak["day"].date()), "peak_day_orders": int(peak["orders"]),
        "peak_multiple": float(peak["orders"] / (nov_orders / 30)),
        "late_share": float(dv.loc["late", "orders"] / dv["orders"].sum()),
        "late_review": float(dv.loc["late", "avg_review"]),
        "ontime_review": float(dv.loc["on time", "avg_review"]),
        "late_bad": float(dv.loc["late", "share_1_2_stars"]),
        "ontime_bad": float(dv.loc["on time", "share_1_2_stars"]),
        "stratified_gap": strat_gap,
        "worst_states": ", ".join(f"{s.state} ({s.late_rate:.0%})" for s in big_states.head(3).itertuples()),
        "repeat_rate": float(r["repeat_customers"]["repeat_rate"].iloc[0]),
        "customers": int(r["repeat_customers"]["customers"].iloc[0]),
        "n_cats": int(len(cat)),
        "n_cats_50": int((cat["cumulative_share"] < 0.5).sum() + 1),
        "n_cats_80": int((cat["cumulative_share"] < 0.8).sum() + 1),
        "top_categories": ", ".join(cat["category"].head(3).str.replace("_", " ")),
    }
    summary = summary_markdown(k)
    (cfg.REPORTS / "executive_summary.md").write_text(summary)
    headline = (f"Olist retail dashboard: revenue +{k['yoy_revenue_growth']:.0%} YoY · "
                f"late orders avg {k['late_review']:.1f}★ vs {k['ontime_review']:.1f}★ · "
                f"repeat rate {k['repeat_rate']:.1%}")
    dashboard.build(r["monthly_kpis"], cat, r["review_by_days_late"], states,
                    r["weekday_hour"], headline, cfg.REPORTS / "dashboard.html")
    with open(cfg.REPORTS / "metrics.json", "w") as f:
        json.dump({"kpis": k, "late_vs_on_time_test": test,
                   "stratified_by_state": strat.round(3).to_dict(orient="records")}, f, indent=2)
    print(summary)
    print(json.dumps(test, indent=2), k["n_cats_80"])


if __name__ == "__main__":
    main()
