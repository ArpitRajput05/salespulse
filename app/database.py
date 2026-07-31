"""
Thin SQLite persistence layer for SalesPulse.
Sales data is ingested via /api/upload and stored as a single table.
"""
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "salespulse.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def save_dataframe(df: pd.DataFrame, table_name: str = "sales") -> None:
    conn = get_connection()
    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()


def load_dataframe(table_name: str = "sales") -> pd.DataFrame:
    if not table_exists(table_name):
        return pd.DataFrame()
    conn = get_connection()
    try:
        return pd.read_sql(f"SELECT * FROM {table_name}", conn, parse_dates=["date"])
    finally:
        conn.close()


def table_exists(table_name: str = "sales") -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return cur.fetchone() is not None
    finally:
        conn.close()
