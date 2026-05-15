"""
data_loader.py
- 從 Google Sheets 讀取 Outo Financial Dashboard 資料
- 提供 fallback 用 mock data
- 用 streamlit cache 加速
"""

import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st


MONTHS_24 = [f"2024-{i:02d}" for i in range(1, 13)] + [f"2025-{i:02d}" for i in range(1, 13)]

# Dashboard (Based on Trip End) 分頁要抓的 row
DASHBOARD_ROWS = {
    "revenue": 6,
    "cogs": 16,
    "gross_profit": 21,
    "gross_margin": 22,
    "operating_expenses": 58,
}

CASHFLOW_ROWS = {
    "guolian_end": 8,
    "outo_hk_end": 13,
    "tanwan_end": 18,
    "aotuo_end": 23,
}

ENTITY_LABELS = {
    "guolian_end": "Guolian (TapPay + 第一銀行)",
    "outo_hk_end": "Outo HK",
    "tanwan_end": "探玩科技 (永豐)",
    "aotuo_end": "奧拓旅行社 (台灣)",
}

# Dashboard 月份對應到欄位字母（B=2024-01, ..., M=2024-12, P=2025-01, ..., AA=2025-12）
# 略過 N=2024 total, O=TREND
DASHBOARD_COL_INDICES = list(range(2, 14)) + list(range(16, 28))


def safe_float(v):
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").replace("%", "").replace("$", "")
    if s.startswith("#") or s == "":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


@st.cache_data(ttl=3600)
def load_from_sheets(sheet_id: str, credentials_path: str):
    """從 Google Sheets 讀取，cache 1 小時"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        st.error("請安裝 `gspread` 跟 `google-auth`：pip install gspread google-auth")
        return None

    if not Path(credentials_path).exists():
        return None

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)

    output = {"months": MONTHS_24, "dashboard": {}, "cashflow": {}}

    ws = sh.worksheet("Dashboard (Based on Trip End)")
    for key, row in DASHBOARD_ROWS.items():
        row_values = ws.row_values(row)
        output["dashboard"][key] = [
            safe_float(row_values[i - 1]) if i - 1 < len(row_values) else 0.0
            for i in DASHBOARD_COL_INDICES
        ]

    ws = sh.worksheet("Cash Flow")
    for key, row in CASHFLOW_ROWS.items():
        row_values = ws.row_values(row)
        output["cashflow"][key] = [safe_float(v) for v in row_values]

    return output


@st.cache_data
def load_mock():
    """讀 mock_data.json (測試用)"""
    p = Path(__file__).parent.parent / "data" / "mock_data.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def load_data(sheet_id: str = None, credentials_path: str = None, use_mock: bool = False):
    """主要入口：依設定回傳資料 dict"""
    if use_mock or not sheet_id or not credentials_path:
        return load_mock()

    data = load_from_sheets(sheet_id, credentials_path)
    if data is None:
        st.warning("⚠ Google Sheets 連線失敗，改用 mock data 顯示")
        return load_mock()
    return data
