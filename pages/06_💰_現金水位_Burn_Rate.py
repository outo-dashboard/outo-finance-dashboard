"""
Outo Finance Dashboard — 現金水位 × Burn Rate × Operating Profit × 情境模擬
==========================================================================
STANDALONE 版本 — 不依賴 sheets_snapshot.json，所有資料 inline。
Sidebar 支援即時情境模擬：銀行水位 / OPEX 變動 / Revenue 變動 / 現金注入 / 固定支出。
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# 資料區（單一改動點）
# ============================================================

MONTHLY_PNL = [
    {"month": "2025-11", "revenue":  7_202_550, "gross_profit": 2_298_368, "opex": 2_666_950},
    {"month": "2025-12", "revenue":  6_500_000, "gross_profit": 4_493_860, "opex": 2_911_985},
    {"month": "2026-01", "revenue":  8_372_840, "gross_profit": 2_557_248, "opex": 1_971_616},
    {"month": "2026-02", "revenue": 10_454_205, "gross_profit": 3_146_914, "opex": 2_572_252},
    {"month": "2026-03", "revenue":  5_205_580, "gross_profit": 1_591_807, "opex": 2_689_983},
    {"month": "2026-04", "revenue":  8_439_130, "gross_profit": 2_107_090, "opex": 3_135_043},
]

BANK_DEFAULTS = [
    {"id": "sinopac",       "label": "永豐銀行",    "entity": "探玩科技",  "balance": 1_314_864},
    {"id": "cathay_united", "label": "國泰世華銀行", "entity": "奧拓旅行社", "balance": 6_000_000},
    {"id": "outo_hk_bank",  "label": "奧拓香港銀行", "entity": "Outo HK",  "balance":   680_000},
    {"id": "tappay",        "label": "TapPay",     "entity": "國聯",      "balance": 8_993_025},
]

DATA_AS_OF = "2026-04"

# ============================================================
# Page config & Bloomberg dark theme
# ============================================================
st.set_page_config(page_title="現金水位 × Burn Rate — Outo", page_icon="💰", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0e1218; }
h1, h2, h3, h4 { color: #f0a830 !important; font-family: 'Noto Sans TC', sans-serif; }
.metric-card { background: #161b22; border: 1px solid #2a3140; border-radius: 4px; padding: 16px 20px; margin-bottom: 8px; }
.metric-label { color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; font-family: 'Noto Sans TC', sans-serif; }
.metric-value { color: #f0a830; font-size: 28px; font-weight: 600; font-family: 'JetBrains Mono', 'Courier New', monospace; margin-top: 4px; }
.metric-sub { color: #c9d1d9; font-size: 12px; font-family: 'JetBrains Mono', monospace; margin-top: 4px; }
.runway-good   { color: #3fb950 !important; }
.runway-warn   { color: #f0a830 !important; }
.runway-danger { color: #f85149 !important; }
.scenario-note { background: #1a1f2e; border-left: 3px solid #f0a830; padding: 8px 12px; margin: 8px 0; font-size: 12px; color: #c9d1d9; border-radius: 2px; }
div[data-testid="stSidebar"] { background-color: #161b22; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Sidebar
# ============================================================
st.sidebar.markdown("## 💰 銀行水位")
st.sidebar.caption("輸入當前餘額")

bank_balances = {}
for b in BANK_DEFAULTS:
    bank_balances[b["id"]] = st.sidebar.number_input(
        f"{b['label']}（{b['entity']}）",
        min_value=0, value=int(b["balance"]), step=10_000, format="%d",
        key=f"bal_{b['id']}",
    )

st.sidebar.markdown("---")
st.sidebar.markdown("## 📊 情境模擬")
st.sidebar.caption("拉滑桿模擬 what-if，下方 runway 即時重算")

opex_adj = st.sidebar.slider("OPEX 調整（%）", -50, 100, 0, 5,
    help="例：凍結招募 → -15%；加開越南辦公室 → +30%")
revenue_adj = st.sidebar.slider("Revenue 調整（%）", -80, 100, 0, 5,
    help="例：旺季 → +20%；衰退 → -30%")
cash_injection = st.sidebar.number_input("一次性現金注入（NT$）",
    min_value=-50_000_000, max_value=100_000_000, value=0, step=500_000, format="%d",
    help="例：信貸下來 +5,000,000；提前還款 -2,000,000")
extra_monthly_cost = st.sidebar.number_input("額外每月固定支出（NT$）",
    min_value=-2_000_000, max_value=5_000_000, value=0, step=50_000, format="%d",
    help="例：新增辦公室租金 +200,000；裁員省下 -500,000")

st.sidebar.markdown("---")
st.sidebar.caption(f"P&L 資料截止：{DATA_AS_OF}")
st.sidebar.caption("資料來源：Leadership Only Google Sheet")

# ============================================================
# 套用情境調整
# ============================================================
df = pd.DataFrame(MONTHLY_PNL)
df["revenue_adj"] = df["revenue"] * (1 + revenue_adj / 100)
df["gross_profit_adj"] = df["gross_profit"] * (1 + revenue_adj / 100)
df["opex_adj"] = df["opex"] * (1 + opex_adj / 100) + extra_monthly_cost
df["operating_profit"] = df["gross_profit_adj"] - df["opex_adj"]
df["net_burn"]   = df["opex_adj"] - df["gross_profit_adj"]
df["gross_burn"] = df["opex_adj"]

total_cash = sum(bank_balances.values()) + cash_injection
avg_net_burn   = df["net_burn"].mean()
avg_gross_burn = df["gross_burn"].mean()

scenario_active = (opex_adj != 0 or revenue_adj != 0 or cash_injection != 0 or extra_monthly_cost != 0)


def runway_str(cash, burn):
    if burn <= 0:
        return "∞ (淨賺中)"
    return f"{cash / burn:.1f} 個月"


def runway_color(cash, burn):
    if burn <= 0:
        return "runway-good"
    m = cash / burn
    if m >= 12: return "runway-good"
    if m >= 6:  return "runway-warn"
    return "runway-danger"


# ============================================================
# Header
# ============================================================
st.title("💰 現金水位 × Burn Rate × 情境模擬")
st.caption(f"Leadership view — 公司目前的錢、燒錢速度、還能燒多久。 Trailing 6 months: {df['month'].iloc[0]} → {df['month'].iloc[-1]}")

if scenario_active:
    parts = []
    if revenue_adj: parts.append(f"Revenue {revenue_adj:+d}%")
    if opex_adj:    parts.append(f"OPEX {opex_adj:+d}%")
    if cash_injection: parts.append(f"現金注入 NT$ {cash_injection:+,}")
    if extra_monthly_cost: parts.append(f"額外固定支出 NT$ {extra_monthly_cost:+,}/月")
    st.markdown(f'<div class="scenario-note"><strong>⚙️ 情境啟用中：</strong>{" · ".join(parts)}</div>', unsafe_allow_html=True)

# ============================================================
# Row 1 — Bank balance cards
# ============================================================
st.markdown("### 銀行水位")
cols = st.columns([1] * len(BANK_DEFAULTS) + [1.2])


def balance_card(col, label, value, sub=""):
    with col:
        st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">NT$ {value:,.0f}</div><div class="metric-sub">{sub}</div></div>', unsafe_allow_html=True)


for i, b in enumerate(BANK_DEFAULTS):
    balance_card(cols[i], b["label"], bank_balances[b["id"]], b["entity"])

total_sub = f"{len(BANK_DEFAULTS)} 個帳戶加總"
if cash_injection:
    total_sub += f" + 注入 NT$ {cash_injection:+,}"
with cols[-1]:
    st.markdown(f'<div class="metric-card" style="border-color: #f0a830;"><div class="metric-label">總可動用現金</div><div class="metric-value">NT$ {total_cash:,.0f}</div><div class="metric-sub">{total_sub}</div></div>', unsafe_allow_html=True)

# ============================================================
# Row 2 — Runway KPI cards
# ============================================================
st.markdown("### Cash Runway（公司還能燒多久）")
r1, r2, r3, r4 = st.columns(4)

with r1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">樂觀情境（Net Burn）</div><div class="metric-value {runway_color(total_cash, avg_net_burn)}">{runway_str(total_cash, avg_net_burn)}</div><div class="metric-sub">未來表現 = 過去 6mo 平均</div></div>', unsafe_allow_html=True)
with r2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">保守情境（Gross Burn）</div><div class="metric-value {runway_color(total_cash, avg_gross_burn)}">{runway_str(total_cash, avg_gross_burn)}</div><div class="metric-sub">營收歸零、只看 OPEX</div></div>', unsafe_allow_html=True)
with r3:
    net_display = f"NT$ {avg_net_burn:,.0f}" if avg_net_burn > 0 else f"NT$ {avg_net_burn:,.0f} (賺)"
    st.markdown(f'<div class="metric-card"><div class="metric-label">6mo 平均 Net Burn</div><div class="metric-value">{net_display}</div><div class="metric-sub">OPEX − Gross Profit</div></div>', unsafe_allow_html=True)
with r4:
    st.markdown(f'<div class="metric-card"><div class="metric-label">6mo 平均 Gross Burn</div><div class="metric-value">NT$ {avg_gross_burn:,.0f}</div><div class="metric-sub">純 OPEX 月均</div></div>', unsafe_allow_html=True)

# ============================================================
# Row 3 — Burn rate dual-line chart
# ============================================================
st.markdown("### Burn Rate 趨勢（Net vs. Gross）")

fig_burn = go.Figure()
fig_burn.add_trace(go.Scatter(x=df["month"], y=df["net_burn"], name="Net Burn (OPEX − GP)",
    mode="lines+markers", line=dict(color="#f0a830", width=3), marker=dict(size=10),
    hovertemplate="<b>%{x}</b><br>Net Burn: NT$ %{y:,.0f}<extra></extra>"))
fig_burn.add_trace(go.Scatter(x=df["month"], y=df["gross_burn"], name="Gross Burn (純 OPEX)",
    mode="lines+markers", line=dict(color="#58a6ff", width=3, dash="dot"), marker=dict(size=10),
    hovertemplate="<b>%{x}</b><br>Gross Burn: NT$ %{y:,.0f}<extra></extra>"))
fig_burn.add_hline(y=0, line=dict(color="#6e7681", width=1, dash="dash"))
fig_burn.update_layout(
    plot_bgcolor="#0e1218", paper_bgcolor="#0e1218",
    font=dict(color="#c9d1d9", family="Noto Sans TC, JetBrains Mono"),
    xaxis=dict(gridcolor="#2a3140", title=None),
    yaxis=dict(gridcolor="#2a3140", title="NTD", tickformat=",.0f"),
    height=400, margin=dict(l=40, r=20, t=20, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
    hovermode="x unified",
)
st.plotly_chart(fig_burn, use_container_width=True)

# ============================================================
# Row 4 — Monthly Operating Profit
# ============================================================
st.markdown("### 月度 Operating Profit（Revenue − COGS − OPEX）")

colors = ["#3fb950" if v > 0 else "#f85149" for v in df["operating_profit"]]
fig_op = go.Figure()
fig_op.add_trace(go.Bar(x=df["month"], y=df["operating_profit"], marker_color=colors,
    text=[f"NT$ {v:,.0f}" for v in df["operating_profit"]], textposition="outside",
    hovertemplate="<b>%{x}</b><br>Operating Profit: NT$ %{y:,.0f}<extra></extra>"))
fig_op.add_hline(y=0, line=dict(color="#6e7681", width=1, dash="dash"))
fig_op.update_layout(
    plot_bgcolor="#0e1218", paper_bgcolor="#0e1218",
    font=dict(color="#c9d1d9", family="Noto Sans TC, JetBrains Mono"),
    xaxis=dict(gridcolor="#2a3140", title=None),
    yaxis=dict(gridcolor="#2a3140", title="NTD", tickformat=",.0f"),
    height=380, margin=dict(l=40, r=20, t=40, b=40), showlegend=False,
)
st.plotly_chart(fig_op, use_container_width=True)

# ============================================================
# Row 5 — Detail table
# ============================================================
with st.expander("📋 月度明細（套用情境後的數字）"):
    show = df[["month", "revenue_adj", "gross_profit_adj", "opex_adj", "operating_profit", "net_burn"]].copy()
    show.columns = ["月份", "Revenue", "Gross Profit", "OPEX", "Operating Profit", "Net Burn"]
    for c in show.columns[1:]:
        show[c] = show[c].apply(lambda x: f"{x:,.0f}")
    st.dataframe(show, use_container_width=True, hide_index=True)

# ============================================================
# Footnote
# ============================================================
st.markdown("---")
st.markdown("""
**計算口徑：**
- **Net Burn** = OPEX − Gross Profit。為負代表該月淨賺。
- **Gross Burn** = 純 OPEX。極端情境下的每月固定成本。
- **Operating Profit** = Revenue − COGS − OPEX。
- **Runway 樂觀** = 總可動用現金 ÷ 6mo 平均 Net Burn（為負則 ∞）。
- **Runway 保守** = 總可動用現金 ÷ 6mo 平均 Gross Burn。

**情境邏輯：**
- Revenue 調整連動 Gross Profit 等比變動（假設毛利率不變）
- OPEX 調整為**比例**，額外固定支出為**金額**（每月加進去）
- 一次性現金注入直接加在總可動用現金（不影響每月 burn）
""")
