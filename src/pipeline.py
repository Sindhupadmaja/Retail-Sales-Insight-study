from pathlib import Path
import matplotlib.pyplot as plt
from analysis import load_sales, summarize

ROOT = Path(__file__).resolve().parents[1]
df = load_sales(ROOT / "data/raw/retail_sales.csv")
monthly, products, categories = summarize(df)

out = ROOT / "reports"
out.mkdir(exist_ok=True)
monthly.to_csv(out / "monthly_revenue.csv", index=False)
products.to_csv(out / "product_performance.csv", index=False)
categories.to_csv(out / "category_performance.csv", index=False)

plt.figure()
plt.plot(monthly["month"], monthly["revenue"], marker="o")
plt.title("Monthly Revenue")
plt.xlabel("Month")
plt.ylabel("Revenue")
plt.tight_layout()
plt.savefig(out / "monthly_revenue.png")
plt.close()
print("Retail analysis complete.")
