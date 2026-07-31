# SalesPulse — Data Analytics Dashboard for Business Insights

An end-to-end data analytics pipeline that ingests raw sales data (CSV/Excel),
cleans and transforms it with **Pandas/NumPy**, stores it in **SQLite**, and
serves interactive **Plotly.js** dashboards through a **FastAPI** backend —
with cached queries to keep the dashboard fast on large datasets.

## Features

- **Ingestion** — upload a CSV or Excel file of raw sales records; invalid
  rows (bad dates, non-numeric prices/quantities, missing fields) are dropped
  during cleaning rather than crashing the pipeline.
- **Transformation** — Pandas derives `revenue`, `month`, and `year` columns
  and normalizes region/product naming before anything is persisted.
- **Storage** — cleaned data is written to a local SQLite database
  (`data/salespulse.db`), so the dashboard survives restarts.
- **Analytics API** — endpoints for KPIs, revenue trend, regional
  performance, and top products, each filterable by region, product, and
  date range.
- **Caching** — query results are cached in memory and invalidated only when
  new data is ingested, so repeat dashboard loads skip recomputation.
- **Dashboard UI** — a vanilla HTML/CSS/JS frontend (no framework) rendering
  interactive Plotly charts with live filtering and drill-down.

## Project Structure

```
salespulse/
├── app/
│   ├── main.py              # FastAPI app + API routes
│   ├── data_processing.py   # Pandas cleaning & aggregation logic
│   ├── database.py          # SQLite persistence layer
│   └── cache.py             # In-memory query cache
├── frontend/
│   ├── index.html           # Dashboard layout
│   ├── style.css            # Styling
│   └── script.js            # Fetches API data, renders Plotly charts
├── data/
│   └── sample_sales.csv     # Synthetic sample dataset (2024–2025)
├── scripts/
│   └── generate_sample_data.py
├── requirements.txt
└── README.md
```

## Getting Started

```bash
# 1. Clone and enter the project
git clone https://github.com/<your-username>/salespulse.git
cd salespulse

# 2. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) regenerate the sample dataset
python3 scripts/generate_sample_data.py

# 5. Run the app
uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000** in your browser. Upload
`data/sample_sales.csv` from the dashboard's "Data Source" panel to see it
populate — or upload your own file with the same column structure.

## Expected Input Format

| Column        | Type   | Notes                                  |
|---------------|--------|-----------------------------------------|
| `date`        | date   | Any parseable date format              |
| `region`      | text   | e.g. North, South, East, West          |
| `product`     | text   | Product name                           |
| `units_sold`  | number | Quantity sold                          |
| `unit_price`  | number | Price per unit                         |

`revenue` is computed automatically as `units_sold × unit_price`.

## API Endpoints

| Method | Endpoint                    | Description                                   |
|--------|------------------------------|-----------------------------------------------|
| POST   | `/api/upload`                | Ingest a CSV/Excel file                       |
| GET    | `/api/filters`                | Available regions, products, date range       |
| GET    | `/api/kpis`                   | Total revenue, units, AOV, MoM growth         |
| GET    | `/api/revenue-trend`          | Time series revenue (monthly/yearly)          |
| GET    | `/api/regional-performance`   | Revenue & units by region                     |
| GET    | `/api/product-performance`    | Top-N products by revenue                     |

All GET endpoints accept optional `region`, `product`, `start_date`, and
`end_date` query parameters for filtering.

## Tech Stack

Python · FastAPI · Pandas · NumPy · SQLite · Plotly.js · HTML/CSS/JavaScript

## Notes

This project was built as a personal portfolio/learning project to
demonstrate an end-to-end analytics workflow: ingestion → cleaning →
storage → querying → visualization.
