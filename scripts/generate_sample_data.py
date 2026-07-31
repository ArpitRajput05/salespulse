"""
Generates a synthetic sales dataset so the dashboard has something to
show immediately after cloning. Run with:  python scripts/generate_sample_data.py
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(seed=42)

REGIONS = ["North", "South", "East", "West"]
PRODUCTS = ["Laptop", "Monitor", "Keyboard", "Mouse", "Webcam", "Headset"]
BASE_PRICES = {
    "Laptop": 750,
    "Monitor": 220,
    "Keyboard": 45,
    "Mouse": 25,
    "Webcam": 60,
    "Headset": 80,
}

dates = pd.date_range("2024-01-01", "2025-12-31", freq="D")
rows = []

for date in dates:
    # more transactions on weekdays, seasonal bump around Nov/Dec
    n_transactions = rng.integers(3, 9)
    if date.month in (11, 12):
        n_transactions += rng.integers(2, 6)

    for _ in range(n_transactions):
        region = rng.choice(REGIONS)
        product = rng.choice(PRODUCTS)
        base_price = BASE_PRICES[product]
        unit_price = round(base_price * rng.uniform(0.9, 1.1), 2)
        units_sold = int(rng.integers(1, 12))

        rows.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "region": region,
                "product": product,
                "units_sold": units_sold,
                "unit_price": unit_price,
            }
        )

df = pd.DataFrame(rows)
out_path = "data/sample_sales.csv"
df.to_csv(out_path, index=False)
print(f"Generated {len(df):,} rows -> {out_path}")
