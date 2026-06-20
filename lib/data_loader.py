"""data_loader.py - 載入 Outo Financial Dashboard Google Sheets 真實資料"""
import json
from pathlib import Path
import streamlit as st


# 29 個月：2024-01 ~ 2026-05
# 2026-05 的營收/銷貨成本/毛利已結帳；OPEX/EBIT 未結帳（snapshot 中為 null）
MONTHS_24 = (
    [f"2024-{i:02d}" for i in range(1, 13)]
    + [f"2025-{i:02d}" for i in range(1, 13)]
    + [f"2026-{i:02d}" for i in range(1, 6)]
)


@st.cache_data(ttl=600, show_spinner="🔄 載入 Google Sheets 資料...")
def load_data(use_mock=False):
    p = Path(__file__).parent.parent / "data" / "sheets_snapshot.json"
    if not p.exists():
        p = Path(__file__).parent.parent / "data" / "mock_data.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))
