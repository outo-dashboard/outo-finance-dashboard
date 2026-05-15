"""
Outo Financial Dashboard - Evidence-Based Edition
資料來源：Outo Financial Dashboard Google Sheets
"""
import streamlit as st
import pandas as pd

from lib.data_loader import load_data, MONTHS_24
from lib.metrics import compute_metrics
from lib import charts as ch


st.set_page_config(
    page_title="Outo Financial Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.markdown("## ⚙️ 設定")
    selected_month = st.selectbox("月份", options=MONTHS_24, index=len(MONTHS_24) - 1)

    st.markdown("---")
    st.markdown("## 📁 資料來源")
    st.caption("🔗 [Outo Financial Dashboard Google Sheets](https://docs.google.com/spreadsheets/d/1-SQGXLw6ROXzIErBpGDXdJYRCOB6oAUAARDo6eeneJI/edit?gid=282172244#gid=282172244)")

    st.markdown("---")
    st.markdown("## 📋 顯示內容")
    st.caption(
        "本儀表板只呈現 Google Sheets 上**完整且可驗證**的真實資料：\n\n"
        "✓ 24 個月營收 / COGS / 毛利 / OPEX\n\n"
        "✓ 23 個月 Pivot Sales / GP / GM%\n\n"
        "✓ 訂單級 AR 預期收款明細\n\n"
        "✓ 32 個產品 GM% 排名\n\n"
        "因資料不足而**未納入**：月度現金部位 trend、月度 AP balance、Runway 模擬"
    )

    st.markdown("---")
    if st.button("🔄 重新載入資料", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


data = load_data()
if data is None:
    st.error("❌ 找不到資料檔")
    st.stop()

idx = MONTHS_24.index(selected_month) if selected_month in MONTHS_24 else len(MONTHS_24) - 1
m = compute_metrics(data, month_idx=idx)


# ============================================================
# Header
# ============================================================
st.markdown(f"# 💰 Outo Financial Dashboard")
st.caption(
    f"**{selected_month}** · 24 個月 trend · 資料同步：{data.get('fetched_at', 'unknown')[:10]} · "
    f"🟢 Google Sheets 真實資料"
)


# ============================================================
# Tabs
# ============================================================
tab1, tab2, tab3 = st.tabs(["📊 損益總覽", "🛒 訂單 & AR 分析", "🔥 成本 & OPEX 結構"])


# ============================================================
# TAB 1 — 損益總覽
# ============================================================
with tab1:
    k = m["kpi"]
    cols = st.columns(6)
    cols[0].metric(f"{selected_month} 月營收",
                   f"NT$ {k['rev_latest']/10000:.0f} 萬",
                   f"MoM {k['mom_pct']:+.1f}%")
    cols[1].metric("月毛利 (EST)",
                   f"NT$ {k['gp_latest']/10000:.0f} 萬",
                   f"毛利率 {k['gm_latest']:.1f}%")
    cols[2].metric("月毛利 (ACT)",
                   f"NT$ {k['act_gp_latest']/10000:.0f} 萬" if k['act_gp_latest'] > 0 else "—",
                   f"實際毛利率 {k['act_gm_latest']:.1f}%" if k['act_gm_latest'] > 0 else "2024 無 ACT 資料")
    cols[3].metric("2025 YTD 累計營收",
                   f"NT$ {k['ytd_2025']/100000000:.2f} 億",
                   f"vs 2024：{k['ytd_yoy']:+.1f}%")
    cols[4].metric("月 OPEX",
                   f"NT$ {k['opex_latest']/10000:.0f} 萬",
                   f"佔營收 {(k['opex_latest']/k['rev_latest']*100):.1f}%" if k['rev_latest'] else "—",
                   delta_color="inverse")
    cols[5].metric("月 EBIT",
                   f"NT$ {k['ebit_latest']/10000:+.0f} 萬",
                   "毛利 − OPEX",
                   delta_color="off")

    st.markdown("---")
    st.markdown("### 📈 月度營收 / 銷貨成本 / 毛利率（24 個月）")
    st.caption("資料來源：Dashboard (Based on Trip End) Row 6 (REALIZED SALES) · Row 16 (ESTIMATED COST OF SALES) · Row 22 (EST. GROSS MARGIN)")
    st.plotly_chart(
        ch.chart_revenue_cogs_gp(m["months"], m["rev"], m["cogs"], m["gp"], m["gm"], idx=idx),
        use_container_width=True
    )

    st.markdown("---")
    st.markdown("### 📊 累計營業額 YTD：2024 vs 2025")
    st.caption(f"YoY 成長：**{k['ytd_yoy']:+.1f}%**（2024 全年 {k['ytd_2024']/100000000:.2f} 億 → 2025 全年 {k['ytd_2025']/100000000:.2f} 億）")
    st.plotly_chart(ch.chart_cumulative_ytd(m["rev"]), use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎯 估計毛利 vs 實際毛利（EST vs ACT）")
    st.caption("EST = Dashboard Row 21 (含交易手續費) · ACT = Dashboard Row 23 (排除 trx/GL/Shopify fees) · 2024 無 ACT 資料")
    st.plotly_chart(
        ch.chart_est_vs_act_gp(m["months"], m["gp"], m["act_gp"], m["gm"], m["act_gm"]),
        use_container_width=True
    )

    st.markdown("---")
    st.markdown("### 📦 本月損益表")
    pnl_df = pd.DataFrame({
        "項目": ["營業收入", "  銷貨成本 (COGS)", "毛利 (EST)", "  營業費用 (OPEX)", "EBIT"],
        "金額 (NTD)": [
            m["rev"][idx], -m["cogs"][idx], m["gp"][idx], -m["opex"][idx], m["ebit"][idx],
        ],
        "佔營收 %": [
            "100.0%",
            f"{-m['cogs'][idx]/m['rev'][idx]*100:.1f}%" if m['rev'][idx] else "—",
            f"{m['gm'][idx]:.1f}%",
            f"{-m['opex'][idx]/m['rev'][idx]*100:.1f}%" if m['rev'][idx] else "—",
            f"{m['ebit'][idx]/m['rev'][idx]*100:.1f}%" if m['rev'][idx] else "—",
        ],
    })
    st.dataframe(pnl_df, hide_index=True, use_container_width=True,
                column_config={"金額 (NTD)": st.column_config.NumberColumn(format="%d")})


# ============================================================
# TAB 2 — 訂單 & AR 分析
# ============================================================
with tab2:
    ar = data.get("ar_by_collection_month", [])
    ar_valid = [a for a in ar if a["month"] != "#N/A"]
    total_ar_amount = sum(a["amount"] for a in ar_valid)
    total_ar_count = sum(a["count"] for a in ar_valid)
    current_month = selected_month
    future_ar = [a for a in ar_valid if a["month"] > current_month]
    future_amount = sum(a["amount"] for a in future_ar)
    future_count = sum(a["count"] for a in future_ar)

    cols = st.columns(4)
    cols[0].metric("總應收金額", f"NT$ {total_ar_amount/10000:.0f} 萬",
                   f"{total_ar_count} 筆訂單")
    cols[1].metric(f"{current_month} 後預期收款", f"NT$ {future_amount/10000:.0f} 萬",
                   f"{future_count} 筆訂單")
    cols[2].metric("追蹤產品數", f"{len(data.get('gm_by_product_top', []))} 個",
                   "Top by GM% trend")
    cols[3].metric("Pivot 月份覆蓋",
                   f"{len(data.get('pivot', {}).get('sales', []))} 個月",
                   f"{data.get('months_pivot_23',[''])[0]} 起")

    st.markdown("---")
    st.markdown("### 🗓 AR 預期收款排程（訂單級資料）")
    st.caption("資料來源：訂單級 AR table（207 筆訂單，依 Est Collection Month group by 月份）· 🔴 = 已過期未收 · 🟢 = 未來預期收款")
    st.plotly_chart(ch.chart_ar_collection(ar_valid, current_month=current_month), use_container_width=True)

    st.markdown("---")
    st.markdown("### 📋 AR 收款明細表")
    ar_df = pd.DataFrame(ar_valid)
    ar_df["狀態"] = ar_df["month"].apply(lambda m: "🔴 已過期" if m <= current_month else "🟢 未來")
    ar_df["平均單筆"] = (ar_df["amount"] / ar_df["count"]).astype(int)
    ar_df.columns = ["預期收款月份", "金額 (NTD)", "訂單數", "狀態", "平均單筆 (NTD)"]
    ar_df = ar_df[["預期收款月份", "狀態", "金額 (NTD)", "訂單數", "平均單筆 (NTD)"]]
    st.dataframe(ar_df, hide_index=True, use_container_width=True,
                column_config={
                    "金額 (NTD)": st.column_config.NumberColumn(format="$ %d"),
                    "平均單筆 (NTD)": st.column_config.NumberColumn(format="$ %d"),
                })

    st.markdown("---")
    st.markdown("### 🏆 Top 10 產品毛利率排名")
    st.caption("資料來源：Pivot Table 1 → Gross Margin by Product（23 個月平均，依 GM% 排序）· 🟢 ≥30% · 🟡 20-29% · 🔴 <20%")
    products = data.get("gm_by_product_top", [])
    if products:
        st.plotly_chart(ch.chart_gm_by_product(products), use_container_width=True)
    else:
        st.info("無產品資料")

    st.markdown("---")
    st.markdown("### 📈 訂單成交 Pivot trend（23 個月）")
    st.caption("資料來源：Pivot Table 1（含預訂與已完成）· 2024-06 → 2026-04")
    piv = data.get("pivot", {})
    if piv.get("sales"):
        st.plotly_chart(
            ch.chart_pivot_sales(data["months_pivot_23"], piv["sales"], piv["gp"], piv["gm"]),
            use_container_width=True
        )


# ============================================================
# TAB 3 — 成本 & OPEX 結構
# ============================================================
with tab3:
    k = m["kpi"]
    cols = st.columns(5)
    cols[0].metric("12 月均 OPEX", f"NT$ {k['avg_opex_12m']/10000:.0f} 萬",
                   "近 12 個月平均")
    cols[1].metric("12 月均營收", f"NT$ {k['avg_revenue_12m']/10000:.0f} 萬",
                   "Run-rate baseline")
    cols[2].metric("12 月均毛利率", f"{k['avg_gm_12m']:.1f}%",
                   "EST GM avg")
    cols[3].metric("OPEX 佔營收", f"{(k['opex_latest']/k['rev_latest']*100):.1f}%" if k['rev_latest'] else "—",
                   f"{selected_month}", delta_color="off")
    cols[4].metric("月均 EBIT", f"NT$ {k['ebit_avg_12m']/10000:+.0f} 萬",
                   "近 12 個月")

    st.markdown("---")
    st.markdown("### 🔥 月度 OPEX 總額 trend")
    st.caption("資料來源：Dashboard Row 58 (OPERATING EXPENSES 合計) · 含 3 個月滾動平均")
    st.plotly_chart(ch.chart_opex_trend(m["months"], m["opex"], m["rolling_3m_opex"]),
                   use_container_width=True)

    st.markdown("---")
    st.markdown("### 📊 主要 OPEX 類別 trend")
    st.caption("資料來源：Dashboard Row 28 (薪資) · Row 29 (軟體) · Row 36 (廣告) · Row 43 (租金) · Row 44 (交通) · 24 個月完整資料")
    st.plotly_chart(
        ch.chart_opex_categories(m["months"], m["salary"], m["software"], m["marketing"], m["rent"], m["transport"]),
        use_container_width=True
    )

    st.markdown("---")
    st.markdown("### 📉 OPEX 佔營收比例（效率指標）")
    st.caption("月度 OPEX / 月度營收。低於 50% 為健康，高於 50% 代表營收波動或費用偏高")
    st.plotly_chart(ch.chart_opex_pct_revenue(m["months"], m["opex_pct_rev"]),
                   use_container_width=True)

    st.markdown("---")
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown(f"### 🥧 {selected_month} COGS 組成")
        st.caption("供應商成本 + 第三方手續費")
        st.plotly_chart(
            ch.chart_cogs_composition(m["vendor_estimated"][idx], m["tappay_fees"][idx], m["guolian_fees"][idx]),
            use_container_width=True
        )
    with col_b:
        st.markdown(f"### 📋 {selected_month} OPEX 細項")
        opex_df = pd.DataFrame({
            "類別": ["薪資", "廣告行銷", "軟體服務", "租金", "交通", "其他"],
            "金額 (NTD)": [
                m["salary"][idx], m["marketing"][idx], m["software"][idx],
                m["rent"][idx], m["transport"][idx],
                m["opex"][idx] - (m["salary"][idx] + m["marketing"][idx] + m["software"][idx] + m["rent"][idx] + m["transport"][idx]),
            ],
        })
        opex_df["佔 OPEX %"] = (opex_df["金額 (NTD)"] / m["opex"][idx] * 100).round(1).astype(str) + "%"
        st.dataframe(opex_df, hide_index=True, use_container_width=True,
                    column_config={"金額 (NTD)": st.column_config.NumberColumn(format="$ %d")})


st.markdown("---")
st.caption(
    "⚠️ **誠實聲明**：本儀表板已**移除**「Runway 情境模擬」「臨時大額支出評估」「可動用資金細項追蹤」"
    "三個原 KPI——因為 Google Sheets 上**缺少月度現金部位歷史**與**月度 AP 餘額歷史**資料，"
    "做出來會是 speculative 而非 evidence-based。要恢復這些功能，需要在 Google Sheets 端先補建立每月底現金/AP 快照 row。"
)
