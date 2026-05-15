"""
data_loader.py - 讀取 Outo Financial Dashboard 真實資料

資料來源：Outo Financial Dashboard Google Sheets
同步機制：透過 Cowork Drive connector 定期拉取最新數據變更至 sheets_snapshot.json
"""

import json
from pathlib import Path

import streamlit as st


SHEET_ID = "1-SQGXLw6ROXzIErBpGDXdJYRCOB6oAUAARDo6eeneJI"

MONTHS_24 = [f"2024-{i:02d}" for i in range(1, 13)] + [f"2025-{i:02d}" for i in range(1, 13)]

ENTITY_LABELS = {
    "guolian_end": "Guolian (TapPay + 第一銀行)",
    "outo_hk_end": "Outo HK",
    "tanwan_end": "探玩科技 (永豐)",
    "aotuo_end": "奧拓旅行社 (台灣)",
}


@st.cache_data(ttl=600, show_spinner="🔄 載入 Google Sheets 資料...")
def load_data(sheet_id=None, credentials_path=None, use_mock=False):
    """讀取 sheets_snapshot.json（來自 Google Sheets 的真實數據快照）"""
    p = Path(__file__).parent.parent / "data" / "sheets_snapshot.json"
    if not p.exists():
        # 向下相容：舊檔名
        p = Path(__file__).parent.parent / "data" / "mock_data.json"
    if not p.exists():
        st.error("❌ 找不到資料檔")
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    data.setdefault("_source", "google_sheets_snapshot")
    return data
