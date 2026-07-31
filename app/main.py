"""
SalesPulse — Data Analytics Dashboard for Business Insights

FastAPI backend that ingests raw sales data (CSV/Excel), cleans and
transforms it with pandas/NumPy, persists it in SQLite, and serves
cached analytics queries to a vanilla JS + Plotly.js frontend.
"""
import io
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import cache, data_processing, database

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="SalesPulse",
    description="Data Analytics Dashboard for Business Insights",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


def _get_data() -> pd.DataFrame:
    return database.load_dataframe()


@app.get("/")
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/api/upload")
async def upload_sales_data(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Please upload a CSV or Excel file.")

    contents = await file.read()
    try:
        if file.filename.lower().endswith(".csv"):
            raw_df = pd.read_csv(io.BytesIO(contents))
        else:
            raw_df = pd.read_excel(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read file: {exc}")

    try:
        clean_df = data_processing.clean_sales_dataframe(raw_df)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if clean_df.empty:
        raise HTTPException(status_code=400, detail="No valid rows found after cleaning.")

    database.save_dataframe(clean_df)
    cache.bump_version()

    return {
        "message": "Data ingested successfully.",
        "rows_ingested": int(len(clean_df)),
        "date_range": [str(clean_df["date"].min().date()), str(clean_df["date"].max().date())],
    }


@app.get("/api/filters")
def get_filters():
    df = _get_data()
    if df.empty:
        return {"regions": [], "products": [], "date_range": None}
    return {
        "regions": sorted(df["region"].unique().tolist()),
        "products": sorted(df["product"].unique().tolist()),
        "date_range": [str(df["date"].min().date()), str(df["date"].max().date())],
    }


@app.get("/api/kpis")
def get_kpis(
    region: Optional[str] = None,
    product: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    key = ("kpis", region, product, start_date, end_date)
    cached = cache.cache_get(key)
    if cached is not None:
        return cached

    df = data_processing.apply_filters(_get_data(), region, product, start_date, end_date)
    result = data_processing.compute_kpis(df)
    cache.cache_set(key, result)
    return result


@app.get("/api/revenue-trend")
def get_revenue_trend(
    granularity: str = "month",
    region: Optional[str] = None,
    product: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    key = ("trend", granularity, region, product, start_date, end_date)
    cached = cache.cache_get(key)
    if cached is not None:
        return cached

    df = data_processing.apply_filters(_get_data(), region, product, start_date, end_date)
    result = data_processing.revenue_trend(df, granularity)
    cache.cache_set(key, result)
    return result


@app.get("/api/regional-performance")
def get_regional_performance(
    product: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    key = ("regional", product, start_date, end_date)
    cached = cache.cache_get(key)
    if cached is not None:
        return cached

    df = data_processing.apply_filters(_get_data(), None, product, start_date, end_date)
    result = data_processing.regional_performance(df)
    cache.cache_set(key, result)
    return result


@app.get("/api/product-performance")
def get_product_performance(
    region: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    top_n: int = 10,
):
    key = ("product", region, start_date, end_date, top_n)
    cached = cache.cache_get(key)
    if cached is not None:
        return cached

    df = data_processing.apply_filters(_get_data(), region, None, start_date, end_date)
    result = data_processing.product_performance(df, top_n)
    cache.cache_set(key, result)
    return result
