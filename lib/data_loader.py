"""
data_loader.py
從 Google Sheets CSV export URL 即時讀取 Outo Financial Dashboard 資料

Real-time 串接：Sheet 設為 Anyone with link can view + Streamlit @st.cache_data(ttl=600) 每 10 分鐘 refresh
Fallback：抓不到時改用 data/mock_data.json
"""
import io
import json
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


SHEET_ID = "1-SQGXLw6ROXzIErBpGDXdJYRCOB6oAUAARDo6eeneJI"
DASHBOARD_GID = 282172244
CASHFLOW_GID = 290014235

CSV_URL = "https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

MONTHS_24 = [f"2024-{i:02d}" for i in range(1, 13)] + [f"2025-{i:02d}" for i in range(1, 13)]

DASHBOARD_COLS = list(range(1, 13)) + list(range(15, 27))

DASHBOARD_ROWS = {
    "revenue": 5,
    "cogs": 15,
    "gross_profit": 20,
    "gross_margin": 21,
    "operating_expenses": 57,
}

ENTITY_LABELS = {
    "guolian_end": "Guolian (TapPay + 第一銀行)",
    "outo_hk_end": "Outo HK",
    "tanwan_end": "探玩科技 (永豐)",
    "aotuo_end": "奧拓旅行社 (台灣)",
}

CASHFLOW_ROWS = {
    "guolian_end": 7,
    "outo_hk_end": 12,
    "tanwan_end": 17,
    "aotuo_end": 22,
}
CASHFLOW_CURRENT_COL = 3


def _safe_float(v):
    if pd.isna(v) or v == "" or v is None:
        return 0.0
    s = str(v).strip().replace(",", "").replace("%", "").replace("$", "")
    if s.startswith("#") or s == "":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


@st.cache_data(ttl=600, show_spinner="🔄 從 Google Sheets 抓取最新資料...")
def fetch_csv(gid):
    url = CSV_URL.format(sheet_id=SHEET_ID, gid=gid)
    resp = requests.get(url, timeout=15, allow_redirects=True)
    resp.raise_for_status()
    text = resp.text
    if text.lstrip().lower().startswith("<!doctype html") or "<html" in text[:500].lower():
        raise PermissionError("Sheet 不是公開的 — 請設定『任何擁有連結的人可檢視』")
    return pd.read_csv(io.StringIO(text), header=None, dtype=str)


def load_from_sheets():
    dashboard_df = fetch_csv(DASHBOARD_GID)
    cashflow_df = fetch_csv(CASHFLOW_GID)
    dashboard = {}
    for key, row_idx in DASHBOARD_ROWS.items():
        if row_idx < len(dashboard_df):
            row = dashboard_df.iloc[row_idx]
            values = [_safe_float(row[c]) if c < len(row) else 0.0 for c in DASHBOARD_COLS]
        else:
            values = [0.0] * 24
        dashboard[key] = values
    cashflow = {}
    for key, row_idx in CASHFLOW_ROWS.items():
        if row_idx < len(cashflow_df):
            row = cashflow_df.iloc[row_idx]
            cashflow[key] = [_safe_float(row[CASHFLOW_CURRENT_COL])] if CASHFLOW_CURRENT_COL < len(row) else [0.0]
        else:
            cashflow[key] = [0.0]
    return {"_source": "google_sheets_live", "months": MONTHS_24, "dashboard": dashboard, "cashflow": cashflow}


@st.cache_data
def load_mock():
    p = Path(__file__).parent.parent / "data" / "mock_data.json"
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    data["_source"] = "mock_data.json (fallback)"
    return data


def load_data(sheet_id=None, credentials_path=None, use_mock=False):
    if use_mock:
        return load_mock()
    try:
        return load_from_sheets()
    except PermissionError as e:
        st.warning(f"⚠ {e}。改用 mock 資料顯示")
        return load_mock()
    except Exception as e:
        st.warning(f"⚠ Google Sheets 抓取失敗（{type(e).__name__}）。改用 mock 資料")
        return load_mock()
