"""Build a self-contained interactive HTML dashboard with Plotly."""
import plotly.graph_objects as go
from plotly.subplots import make_subplots

WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def build(monthly, categories, delivery_curve, states, heat, headline, path):
    fig = make_subplots(
        rows=3, cols=2, vertical_spacing=0.09, horizontal_spacing=0.1,
        specs=[[{"secondary_y": True}, {}], [{}, {}], [{"colspan": 2}, None]],
        subplot_titles=("Monthly revenue and orders", "Top 15 categories by revenue",
                        "Review score vs days late (negative = early)", "Late-delivery rate by state (top 12 by revenue)",
                        "Orders by weekday and hour"))
    fig.add_bar(x=monthly["order_month"], y=monthly["revenue"], name="Revenue (R$)", row=1, col=1)
    fig.add_scatter(x=monthly["order_month"], y=monthly["orders"], name="Orders", mode="lines+markers",
                    row=1, col=1, secondary_y=True)
    top = categories.head(15).iloc[::-1]
    fig.add_bar(x=top["revenue"], y=top["category"], orientation="h", name="Category revenue",
                row=1, col=2, showlegend=False)
    fig.add_scatter(x=delivery_curve["days_vs_estimate"], y=delivery_curve["avg_review"],
                    mode="lines+markers", name="Avg review", row=2, col=1, showlegend=False)
    s = states.head(12)
    fig.add_bar(x=s["state"], y=s["late_rate"], name="Late rate", row=2, col=2, showlegend=False)
    pivot = heat.pivot(index="weekday", columns="hour", values="orders")
    fig.add_heatmap(z=pivot.values, x=list(pivot.columns), y=[WEEKDAYS[i] for i in pivot.index],
                    colorscale="Blues", row=3, col=1, showscale=False)
    fig.update_layout(height=1250, title=headline, template="plotly_white",
                      legend=dict(orientation="h", y=1.04, x=0))
    fig.write_html(path, include_plotlyjs="cdn")
