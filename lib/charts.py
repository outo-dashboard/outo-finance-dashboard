"""
charts.py - 用 Plotly 畫圖（Streamlit 內建支援，互動性佳）
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots


COLORS = {
    "primary": "#2563eb",
    "success": "#16a34a",
    "danger": "#dc2626",
    "warning": "#ea580c",
    "neutral": "#64748b",
    "blue_light": "#bfdbfe",
    "green_light": "#86efac",
    "orange_light": "#fed7aa",
}


def chart_revenue_margin(months, revenue, gross_profit, gross_margin):
    """營收 + 毛利 (bar) + 毛利率 (line, 右軸)"""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(name="營收", x=months, y=revenue, marker_color=COLORS["blue_light"], hovertemplate="%{x}<br>營收：%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(name="毛利", x=months, y=gross_profit, marker_color=COLORS["green_light"], hovertemplate="%{x}<br>毛利：%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(name="毛利率 %", x=months, y=gross_margin, mode="lines+markers", line=dict(color=COLORS["danger"], width=2), hovertemplate="%{x}<br>毛利率：%{y:.1f}%<extra></extra>"), secondary_y=True)
    fig.update_layout(
        barmode="group",
        height=380,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="NTD", secondary_y=False)
    fig.update_yaxes(title_text="毛利率 %", secondary_y=True, range=[0, 50])
    return fig


def chart_cumulative(months_x, cum_2024, cum_2025):
    fig = go.Figure()
    fig.add_trace(go.Scatter(name="2024 累計", x=months_x, y=cum_2024, mode="lines+markers", line=dict(color=COLORS["neutral"], width=2)))
    fig.add_trace(go.Scatter(name="2025 累計", x=months_x, y=cum_2025, mode="lines+markers", line=dict(color=COLORS["primary"], width=3), fill="tozeroy", fillcolor="rgba(37,99,235,0.08)"))
    fig.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        yaxis_title="累計營業額 (NTD)",
    )
    return fig


def chart_apar(months, revenue, cogs):
    """AR/AP 估算趨勢（用 revenue/cogs 反推）"""
    ar = [r * 0.32 for r in revenue]
    ap = [c * 0.38 for c in cogs]
    fig = go.Figure()
    fig.add_trace(go.Scatter(name="AR 應收（預期現金流入）", x=months, y=ar, mode="lines", line=dict(color=COLORS["success"], width=2), fill="tozeroy", fillcolor="rgba(22,163,74,0.15)"))
    fig.add_trace(go.Scatter(name="AP 應付（預期現金流出）", x=months, y=ap, mode="lines", line=dict(color=COLORS["danger"], width=2), fill="tozeroy", fillcolor="rgba(220,38,38,0.15)"))
    fig.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        yaxis_title="NTD",
    )
    return fig


def chart_burn(months, opex, rolling):
    fig = make_subplots(specs=[[{"secondary_y": False}]])
    fig.add_trace(go.Bar(name="月度 OPEX", x=months, y=opex, marker_color=COLORS["orange_light"], hovertemplate="%{x}<br>OPEX：%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(name="3 個月滾動平均", x=months, y=rolling, mode="lines+markers", line=dict(color=COLORS["danger"], width=2)))
    fig.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        yaxis_title="NTD",
    )
    return fig


def chart_opex_breakdown(breakdown):
    labels = list(breakdown.keys())
    values = list(breakdown.values())
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values,
        hole=0.5,
        marker=dict(colors=["#3b82f6","#16a34a","#dc2626","#f59e0b","#8b5cf6","#06b6d4","#ec4899","#64748b"]),
        hovertemplate="%{label}<br>%{value:,.0f} NTD (%{percent})<extra></extra>",
    )])
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
    return fig


def chart_cash_projection(available, scenarios, months_ahead=12):
    """情境模擬：未來 N 個月現金部位"""
    fig = go.Figure()
    x = [f"M+{i}" for i in range(months_ahead + 1)]
    for key, color, name in [
        ("worst", COLORS["danger"], "最差情境 (營收×50%)"),
        ("neutral", COLORS["primary"], "中性情境 (12月均)"),
        ("best", COLORS["success"], "最好情境 (營收×130%)"),
    ]:
        runway = scenarios[key]["runway"]
        if runway is None:
            # 正現金流：往上漲
            y = [available + i * (available * 0.02) for i in range(months_ahead + 1)]
        else:
            monthly_burn = available / runway
            y = [max(available - i * monthly_burn, 0) for i in range(months_ahead + 1)]
        fig.add_trace(go.Scatter(name=name, x=x, y=y, mode="lines+markers", line=dict(color=color, width=2)))
    fig.add_hline(y=0, line_dash="dash", line_color=COLORS["danger"], annotation_text="現金歸零")
    fig.update_layout(
        height=350,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        yaxis_title="現金部位 (NTD)",
    )
    return fig
