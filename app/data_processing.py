"""
Data cleaning, transformation, and aggregation logic for SalesPulse.
Keeps all pandas/numpy work isolated from the API layer.
"""
import pandas as pd

REQUIRED_COLUMNS = ["date", "region", "product", "units_sold", "unit_price"]


def clean_sales_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names, coerce types, drop bad rows, and derive revenue."""
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    df["region"] = df["region"].astype(str).str.strip().str.title()
    df["product"] = df["product"].astype(str).str.strip().str.title()

    df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df = df.dropna(subset=["units_sold", "unit_price"])
    df = df[(df["units_sold"] > 0) & (df["unit_price"] > 0)]

    df["revenue"] = df["units_sold"] * df["unit_price"]
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.to_period("M").astype(str)

    df = df.drop_duplicates().reset_index(drop=True)
    return df


def apply_filters(df: pd.DataFrame, region=None, product=None, start_date=None, end_date=None) -> pd.DataFrame:
    if df.empty:
        return df
    filtered = df
    if region:
        filtered = filtered[filtered["region"] == region]
    if product:
        filtered = filtered[filtered["product"] == product]
    if start_date:
        filtered = filtered[filtered["date"] >= pd.to_datetime(start_date)]
    if end_date:
        filtered = filtered[filtered["date"] <= pd.to_datetime(end_date)]
    return filtered


def compute_kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_revenue": 0,
            "total_units": 0,
            "avg_order_value": 0,
            "num_transactions": 0,
            "mom_growth_pct": None,
        }

    total_revenue = float(df["revenue"].sum())
    total_units = int(df["units_sold"].sum())
    num_transactions = int(len(df))
    avg_order_value = round(total_revenue / num_transactions, 2) if num_transactions else 0

    monthly = df.groupby("month")["revenue"].sum().sort_index()
    mom_growth = None
    if len(monthly) >= 2:
        prev, curr = monthly.iloc[-2], monthly.iloc[-1]
        if prev:
            mom_growth = round(((curr - prev) / prev) * 100, 2)

    return {
        "total_revenue": round(total_revenue, 2),
        "total_units": total_units,
        "avg_order_value": avg_order_value,
        "num_transactions": num_transactions,
        "mom_growth_pct": mom_growth,
    }


def revenue_trend(df: pd.DataFrame, granularity: str = "month") -> list:
    if df.empty:
        return []
    key = "month" if granularity == "month" else "year"
    grouped = df.groupby(key)["revenue"].sum().sort_index()
    return [{"period": str(idx), "revenue": round(val, 2)} for idx, val in grouped.items()]


def regional_performance(df: pd.DataFrame) -> list:
    if df.empty:
        return []
    grouped = (
        df.groupby("region")
        .agg(revenue=("revenue", "sum"), units_sold=("units_sold", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    grouped["revenue"] = grouped["revenue"].round(2)
    return grouped.to_dict(orient="records")


def product_performance(df: pd.DataFrame, top_n: int = 10) -> list:
    if df.empty:
        return []
    grouped = (
        df.groupby("product")
        .agg(revenue=("revenue", "sum"), units_sold=("units_sold", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
        .head(top_n)
    )
    grouped["revenue"] = grouped["revenue"].round(2)
    return grouped.to_dict(orient="records")
