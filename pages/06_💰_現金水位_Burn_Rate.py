"""
Outo Finance Dashboard — 現金水位 × Burn Rate × Operating Profit
================================================================
Drop-in Streamlit page. Save as `pages/06_💰_現金水位_Burn_Rate.py`
in https://github.com/outo-dashboard/outo-finance-dashboard.

Data source: `data/sheets_snapshot.json` (single source of truth).
Update the JSON to refresh dashboard numbers — no code change needed.
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# Page config & theme (Bloomberg Terminal dark, amber accent)
# ============================================================
st.set_page_config(
    page_title="現金水位 × Burn Rate — Outo",
    page_icon="💰",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1218; }
    h1, h2, h3, h4 { color: #f0a830 !important; font-family: 'Noto Sans TC', sans-serif; }
    .metric-card {
        background: #161b22;
        border: 1px solid #2a3140;
        border-radius: 4px;
        padding: 16px 20px;
        margin-bottom: 8px;
    }
    .metric-label {
        color: #8b949e;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-family: 'Noto Sans TC', sans-serif;
    }
    .metric-value {
        color: #f0a830;
        font-size: 28px;
        font-weight: 600;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        margin-top: 4px;
    }
    .metric-sub {
        color: #c9d1d9;
        font-size: 12px;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 4px;
    }
    .runway-good   { color: #3fb950 !important; }
    .runway-warn   { color: #f0a830 !important; }
    .runway-danger { color: #f85149 !important; }
    div[data-testid="stSidebar"] { background-color: #161b22; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# Load data from sheets_snapshot.json
# ============================================================
SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "data" / "sheets_snapshot.json"


@st.cache_data(ttl=60)
def load_snapshot():
    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


snap = load_snapshot()
meta = snap["meta"]
banks = snap["bank_balances"]["accounts"]

df = pd.DataFrame(snap["monthly_pnl"])
df["operating_profit"] = df["gross_profit"] - df["opex"]
df["net_burn"] = df["opex"] - df["gross_profit"]
df["gross_burn"] = df["opex"]

# Trailing 6 months (sorted ascending)
df_t6 = df.sort_values("month").tail(6).reset_index(drop=True)

# ============================================================
# Sidebar — bank balance inputs (default from JSON)
# ============================================================
st.sidebar.markdown("### 💰 銀行水位（即時輸入）")
st.sidebar.caption("輸入當前餘額，下方 runway 即時重算。預設值來自 sheets_snapshot.json。")

bank_inputs = {}
for b in banks:
    bank_inputs[b["id"]] = st.sidebar.number_input(
        f"{b['label']}（{b['entity']}）",
        min_value=0,
        value=int(b["balance"]),
        step=10_000,
        format="%d",
        key=f"bank_{b['id']}",
    )

st.sidebar.markdown("---")
st.sidebar.caption(f"資料截止：{meta.get('last_updated', 'N/A')[:10]}")
st.sidebar.caption(f"來源：{meta.get('source', '—')}")

total_cash = sum(bank_inputs.values())

# ============================================================
# Burn rate calculations
# ============================================================
avg_net_burn = df_t6["net_burn"].mean()       # 可能為負（淨賺）
avg_gross_burn = df_t6["gross_burn"].mean()   # 恆正


def runway_str(cash: float, burn: float) -> str:
    if burn <= 0:
        return "∞ (淨賺中)"
    return f"{cash / burn:.1f} 個月"


def runway_color(cash: float, burn: float) -> str:
    if burn <= 0:
        return "runway-good"
    months = cash / burn
    if months >= 12:
        return "runway-good"
    if months >= 6:
        return "runway-warn"
    return "runway-danger"


# ============================================================
# Header
# ============================================================
st.title("💰 現金水位 × Burn Rate × Operating Profit")
st.caption(
    f"Leadership view — 公司目前的錢、燒錢速度、還能燒多久。"
    f" Trailing 6 months: {df_t6['month'].iloc[0]} → {df_t6['month'].iloc[-1]}"
)

# ============================================================
# Row 1 — Bank balance cards
# ============================================================
st.markdown("### 銀行水位")
cols = st.columns([1] * len(banks) + [1.2])


def balance_card(col, label, value, sub=""):
    with col:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">NT$ {value:,.0f}</div>
                <div class="metric-sub">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


for i, b in enumerate(banks):
    balance_card(cols[i], b["label"], bank_inputs[b["id"]], b["entity"])

with cols[-1]:
    st.markdown(
        f"""
        <div class="metric-card" style="border-color: #f0a830;">
            <div class="metric-label">總現金水位</div>
            <div class="metric-value">NT$ {total_cash:,.0f}</div>
            <div class="metric-sub">{len(banks)} 個帳戶加總</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# Row 2 — Runway KPI cards
# ============================================================
st.markdown("### Cash Runway（公司還能燒多久）")
r1, r2, r3, r4 = st.columns(4)

with r1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">樂觀情境（Net Burn）</div>
            <div class="metric-value {runway_color(total_cash, avg_net_burn)}">
                {runway_str(total_cash, avg_net_burn)}
            </div>
            <div class="metric-sub">未來表現 = 過去 6mo 平均</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with r2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">保守情境（Gross Burn）</div>
            <div class="metric-value {runway_color(total_cash, avg_gross_burn)}">
                {runway_str(total_cash, avg_gross_burn)}
            </div>
            <div class="metric-sub">營收歸零、只看 OPEX</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with r3:
    net_display = (
        f"NT$ {avg_net_burn:,.0f}"
        if avg_net_burn > 0
        else f"NT$ {avg_net_burn:,.0f} (賺)"
    )
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">6mo 平均 Net Burn</div>
            <div class="metric-value">{net_display}</div>
            <div class="metric-sub">OPEX − Gross Profit</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with r4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">6mo 平均 Gross Burn</div>
            <div class="metric-value">NT$ {avg_gross_burn:,.0f}</div>
            <div class="metric-sub">純 OPEX 月均</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# Row 3 — Burn rate dual-line chart
# ============================================================
st.markdown("### Burn Rate 趨勢（Net vs. Gross）")

fig_burn = go.Figure()
fig_burn.add_trace(
    go.Scatter(
        x=df_t6["month"],
        y=df_t6["net_burn"],
        name="Net Burn (OPEX − GP)",
        mode="lines+markers",
        line=dict(color="#f0a830", width=3),
        marker=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Net Burn: NT$ %{y:,.0f}<extra></extra>",
    )
)
fig_burn.add_trace(
    go.Scatter(
        x=df_t6["month"],
        y=df_t6["gross_burn"],
        name="Gross Burn (純 OPEX)",
        mode="lines+markers",
        line=dict(color="#58a6ff", width=3, dash="dot"),
        marker=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Gross Burn: NT$ %{y:,.0f}<extra></extra>",
    )
)
fig_burn.add_hline(y=0, line=dict(color="#6e7681", width=1, dash="dash"))
fig_burn.update_layout(
    plot_bgcolor="#0e1218",
    paper_bgcolor="#0e1218",
    font=dict(color="#c9d1d9", family="Noto Sans TC, JetBrains Mono"),
    xaxis=dict(gridcolor="#2a3140", title=None),
    yaxis=dict(gridcolor="#2a3140", title="NTD", tickformat=",.0f"),
    height=400,
    margin=dict(l=40, r=20, t=20, b=40),
    legend=dict(
        orientation="h",
        yanchor="bottom", y=1.02,
        xanchor="right", x=1,
        bgcolor="rgba(0,0,0,0)",
    ),
    hovermode="x unified",
)
st.plotly_chart(fig_burn, use_container_width=True)

# ============================================================
# Row 4 — Monthly Operating Profit
# ============================================================
st.markdown("### 月度 Operating Profit（Revenue − COGS − OPEX）")

colors = ["#3fb950" if v > 0 else "#f85149" for v in df_t6["operating_profit"]]
fig_op = go.Figure()
fig_op.add_trace(
    go.Bar(
        x=df_t6["month"],
        y=df_t6["operating_profit"],
        marker_color=colors,
        text=[f"NT$ {v:,.0f}" for v in df_t6["operating_profit"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Operating Profit: NT$ %{y:,.0f}<extra></extra>",
    )
)
fig_op.add_hline(y=0, line=dict(color="#6e7681", width=1, dash="dash"))
fig_op.update_layout(
    plot_bgcolor="#0e1218",
    paper_bgcolor="#0e1218",
    font=dict(color="#c9d1d9", family="Noto Sans TC, JetBrains Mono"),
    xaxis=dict(gridcolor="#2a3140", title=None),
    yaxis=dict(gridcolor="#2a3140", title="NTD", tickformat=",.0f"),
    height=380,
    margin=dict(l=40, r=20, t=40, b=40),
    showlegend=False,
)
st.plotly_chart(fig_op, use_container_width=True)

# ============================================================
# Row 5 — Detail table
# ============================================================
with st.expander("📋 月度明細 — Revenue / Gross Profit / OPEX / Op. Profit"):
    show = df_t6[["month", "revenue", "gross_profit", "opex", "operating_profit", "net_burn"]].copy()
    show.columns = ["月份", "Revenue", "Gross Profit", "OPEX", "Operating Profit", "Net Burn"]
    for c in show.columns[1:]:
        show[c] = show[c].apply(lambda x: f"{x:,.0f}")
    st.dataframe(show, use_container_width=True, hide_index=True)

# ============================================================
# Footnote
# ============================================================
st.markdown("---")
st.markdown(
    """
    **計算口徑：**
    - **Net Burn** = OPEX − Gross Profit。為負代表該月淨賺。
    - **Gross Burn** = 純 OPEX。極端情境下的每月固定成本。
    - **Operating Profit** = Revenue − COGS − OPEX。
    - **Runway 樂觀** = 總現金 ÷ 6mo 平均 Net Burn（若為負則 ∞）。
    - **Runway 保守** = 總現金 ÷ 6mo 平均 Gross Burn。

    **資料更新方式：** 改 `data/sheets_snapshot.json` 後 commit → Streamlit Cloud auto-redeploy。
    """
)
