"""
Outo Financial Dashboard - Streamlit App
回答 leadership 六大問題的財務儀表板
"""

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from lib.data_loader import load_data, MONTHS_24
from lib.metrics import compute_all_metrics, assess_large_expense
from lib import charts as ch


# ============================================================
# 頁面設定
# ============================================================
st.set_page_config(
    page_title="Outo Financial Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Sidebar：設定
# ============================================================
with st.sidebar:
    st.markdown("## ⚙️ 設定")

    selected_month = st.selectbox("月份", options=MONTHS_24, index=len(MONTHS_24) - 1)

    selected_entities = st.multiselect(
        "Entity",
        options=["國聯（台灣）", "Outo HK（香港）", "探玩科技（台灣）", "奧拓旅行社（台灣）", "Outo SG（新加坡）"],
        default=["國聯（台灣）", "Outo HK（香港）", "探玩科技（台灣）", "奧拓旅行社（台灣）"],
    )

    st.markdown("---")
    st.markdown("## 📁 資料來源")

    use_mock = st.checkbox("使用 mock data（測試用）", value=True)

    default_sheet_id = os.getenv("OUTO_SHEET_ID", "1-SQGXLw6ROXzIErBpGDXdJYRCOB6oAUAARDo6eeneJI")
    sheet_id = st.text_input("Google Sheets ID", value=default_sheet_id, disabled=use_mock)

    default_creds = os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
    credentials_path = st.text_input("Service Account credentials.json 路徑", value=default_creds, disabled=use_mock)

    st.markdown("---")
    if st.button("🔄 重新載入資料", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ============================================================
# 載入資料 + 計算指標
# ============================================================
data = load_data(sheet_id=sheet_id, credentials_path=credentials_path, use_mock=use_mock)

if data is None:
    st.error("❌ 無法載入資料。請確認 mock_data.json 存在，或設定 Google Sheets credentials。")
    st.stop()

target_idx = MONTHS_24.index(selected_month) if selected_month in MONTHS_24 else len(MONTHS_24) - 1
m = compute_all_metrics(data, target_month_idx=target_idx)


# ============================================================
# Header
# ============================================================
st.markdown(f"# 💰 Outo Financial Dashboard — {selected_month}")
entity_text = "、".join([e.split("（")[0] for e in selected_entities]) if selected_entities else "全部"
st.caption(f"Leadership 六大關鍵問題 · Entity：{entity_text} · 資料更新即時")


# ============================================================
# Tabs
# ============================================================
tab1, tab2 = st.tabs(["📊 本月報表", "📈 月趨勢"])


# ============================================================
# Tab 1: 本月報表
# ============================================================
with tab1:
    # ---------- KPI 快覽 ----------
    st.markdown("### 📊 KPI 快覽")

    k = m["kpi"]
    cols = st.columns(6)
    cols[0].metric(
        label=f"{selected_month} 月營收",
        value=f"NT$ {k['last_revenue']/10000:.0f} 萬",
        delta=f"MoM {k['mom_pct']:+.1f}%",
        help="當月已完成營收（After Discount）"
    )
    cols[1].metric(
        label="月毛利",
        value=f"NT$ {k['gross_profit']/10000:.0f} 萬",
        delta=f"毛利率 {k['gross_margin']:.1f}%",
        help="毛利 = 營收 - COGS"
    )
    cols[2].metric(
        label="2025 YTD 累計",
        value=f"NT$ {k['ytd_2025']/100000000:.2f} 億",
        delta=f"vs 2024: {(k['ytd_2025']/k['ytd_2024']-1)*100:+.1f}%" if k['ytd_2024'] else None,
        help="2025 年累計營收 vs 2024 同期"
    )
    cols[3].metric(
        label="可動用資金",
        value=f"NT$ {k['available']/10000:.0f} 萬",
        delta=f"現金 {k['total_cash']/10000:.0f} 萬",
        help="現金 + AR - AP"
    )
    cols[4].metric(
        label="Runway（中性）",
        value="∞" if k['runway_neutral'] is None else f"{k['runway_neutral']:.1f} 個月",
        delta="正現金流" if k['runway_neutral'] is None else "需注意",
        delta_color="normal" if k['runway_neutral'] is None else "inverse",
        help="按 12 月平均營收 + OPEX 計算"
    )
    cols[5].metric(
        label="下月預測",
        value=f"NT$ {k['next_forecast']/10000:.0f} 萬",
        delta=f"近 3 月均值",
        help="近 3 個月營收平均做為下月線性預測"
    )

    st.markdown("---")

    # ---------- 本月損益細項 ----------
    st.markdown("### 📦 本月損益")
    col_a, col_b = st.columns([2, 1])

    with col_a:
        pnl_df = pd.DataFrame({
            "項目": ["營業收入", "  銷貨成本", "毛利", "  營業費用 (OPEX)", "EBIT"],
            "金額 (NTD)": [
                m["revenue"][target_idx],
                -m["cogs"][target_idx],
                m["gross_profit"][target_idx],
                -m["opex"][target_idx],
                m["ebit"][target_idx],
            ],
            "佔營收 %": [
                "100.0%",
                f"{-m['cogs'][target_idx]/m['revenue'][target_idx]*100:.1f}%" if m['revenue'][target_idx] else "—",
                f"{m['gross_margin'][target_idx]:.1f}%",
                f"{-m['opex'][target_idx]/m['revenue'][target_idx]*100:.1f}%" if m['revenue'][target_idx] else "—",
                f"{m['ebit'][target_idx]/m['revenue'][target_idx]*100:.1f}%" if m['revenue'][target_idx] else "—",
            ],
        })
        st.dataframe(pnl_df, hide_index=True, use_container_width=True, column_config={
            "金額 (NTD)": st.column_config.NumberColumn(format="%d"),
        })

    with col_b:
        st.plotly_chart(ch.chart_opex_breakdown(m["opex_breakdown"]), use_container_width=True)
        st.caption("OPEX 結構（最新月估算）")

    st.markdown("---")

    # ---------- AP/AR + 可動用資金 ----------
    st.markdown("### 💰 Q1+Q5：AP/AR 現況 + 可動用資金")
    cash_df = pd.DataFrame(m["cash_by_entity"])
    cash_df["available"] = cash_df["cash"] + cash_df["ar"] - cash_df["ap"]
    cash_df.columns = ["Entity", "現金部位", "AR 應收", "AP 應付", "可動用 (Cash+AR-AP)"]
    total_row = pd.DataFrame([{
        "Entity": "**合計**",
        "現金部位": cash_df["現金部位"].sum() + m["apar"]["already_received"],
        "AR 應收": m["apar"]["receivable"],
        "AP 應付": m["apar"]["payable"],
        "可動用 (Cash+AR-AP)": k["available"],
    }])
    full_df = pd.concat([cash_df, total_row], ignore_index=True)
    st.dataframe(full_df, hide_index=True, use_container_width=True, column_config={
        "現金部位": st.column_config.NumberColumn(format="$ %d"),
        "AR 應收": st.column_config.NumberColumn(format="$ %d"),
        "AP 應付": st.column_config.NumberColumn(format="$ %d"),
        "可動用 (Cash+AR-AP)": st.column_config.NumberColumn(format="$ %d"),
    })
    st.caption("💡 各 entity 現金部位來自 Google Sheets Cash Flow 分頁，AR/AP 來自 Dashboard rows 7-8 / 18-19")

    st.markdown("---")

    # ---------- Q4: 大額支出評估 ----------
    st.markdown("### 🎯 Q4：臨時大額支出評估")
    col_in, col_out = st.columns([1, 2])
    with col_in:
        amount = st.number_input(
            "欲評估的支出金額（NTD）",
            min_value=0, max_value=100000000,
            value=2000000, step=100000,
            format="%d",
        )
    with col_out:
        result = assess_large_expense(amount, m)
        if result["level"] == "ok":
            st.success(f"{result['color']} {result['msg']}")
        elif result["level"] == "warn":
            st.warning(f"{result['color']} {result['msg']}")
        else:
            st.error(f"{result['color']} {result['msg']}")

    st.markdown("---")

    # ---------- Q3: 極端情境模擬 ----------
    st.markdown("### 📉 Q3：極端情境模擬 Runway")
    sc_cols = st.columns(3)
    for i, (key, name, color) in enumerate([
        ("worst", "最差（營收 × 50%）", "🔴"),
        ("neutral", "中性（12 月均）", "🔵"),
        ("best", "最好（營收 × 130%）", "🟢"),
    ]):
        runway = m["scenarios"][key]["runway"]
        with sc_cols[i]:
            st.markdown(f"**{color} {name}**")
            if runway is None:
                st.markdown(f"### ∞")
                st.caption("正現金流，無 runway 風險")
            else:
                st.markdown(f"### {runway:.1f} 個月")
                st.caption(f"當前可動用 ÷ 月淨流出")

    st.plotly_chart(
        ch.chart_cash_projection(k["available"], m["scenarios"], months_ahead=12),
        use_container_width=True
    )


# ============================================================
# Tab 2: 月趨勢
# ============================================================
with tab2:
    # 時間範圍切換
    range_choice = st.radio(
        "時間範圍",
        options=["近 6 個月", "近 12 個月", "完整 24 個月"],
        index=1,
        horizontal=True,
    )
    n = {"近 6 個月": 6, "近 12 個月": 12, "完整 24 個月": 24}[range_choice]

    months_show = m["months"][-n:]
    rev_show = m["revenue"][-n:]
    gp_show = m["gross_profit"][-n:]
    gm_show = m["gross_margin"][-n:]
    opex_show = m["opex"][-n:]
    rolling_show = m["rolling_3m_opex"][-n:]
    cogs_show = m["cogs"][-n:]

    st.markdown("### 📈 Q6：營業額即時監控")
    st.caption("月度營收、毛利、毛利率")
    st.plotly_chart(
        ch.chart_revenue_margin(months_show, rev_show, gp_show, gm_show),
        use_container_width=True
    )

    st.markdown("---")

    st.markdown("### 📊 累計營業額（YTD）2024 vs 2025")
    cum_2024, cum_2025, s24, s25 = [], [], 0, 0
    for i in range(12):
        s24 += m["revenue"][i]; cum_2024.append(s24)
        s25 += m["revenue"][i + 12]; cum_2025.append(s25)
    month_labels = [f"{i}月" for i in range(1, 13)]
    st.plotly_chart(ch.chart_cumulative(month_labels, cum_2024, cum_2025), use_container_width=True)

    st.markdown("---")

    st.markdown("### 💸 Q1：AP/AR 趨勢（估算）")
    st.caption("AR 應收（綠）vs AP 應付（紅）的月度趨勢")
    st.plotly_chart(ch.chart_apar(months_show, rev_show, cogs_show), use_container_width=True)

    st.markdown("---")

    st.markdown("### 🔥 Q2：Burn Rate 趨勢")
    st.caption("月度 OPEX + 3 個月滾動平均")
    st.plotly_chart(ch.chart_burn(months_show, opex_show, rolling_show), use_container_width=True)


# ============================================================
# Footer
# ============================================================
st.markdown("---")
st.caption(
    "🛠 Built with Streamlit · 資料來自 Outo Financial Dashboard Google Sheets · "
    f"24 個月：{m['months'][0]} ~ {m['months'][-1]}"
)
