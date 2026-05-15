"""charts.py - Plotly chart functions for Outo Financial Dashboard"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots

C = {
    "primary": "#2563eb", "success": "#16a34a", "danger": "#dc2626",
    "warning": "#ea580c", "neutral": "#64748b",
    "blue_l": "#bfdbfe", "green_l": "#86efac", "orange_l": "#fed7aa",
    "red_l": "#fecaca", "purple": "#8b5cf6", "cyan": "#06b6d4",
}


def chart_revenue_cogs_gp(months, rev, cogs, gp, gm, idx=None):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(name="營業收入", x=months, y=rev, marker_color=C["blue_l"],
                        hovertemplate="%{x}<br>營收：NT$ %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(name="銷貨成本", x=months, y=[-c for c in cogs], marker_color=C["red_l"],
                        hovertemplate="%{x}<br>COGS：NT$ %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(name="毛利率 %", x=months, y=gm, mode="lines+markers",
                            line=dict(color=C["success"], width=3),
                            marker=dict(size=8),
                            hovertemplate="%{x}<br>毛利率：%{y:.1f}%<extra></extra>"),
                  secondary_y=True)
    if idx is not None and 0 <= idx < len(months):
        fig.add_vline(x=months[idx], line_dash="dot", line_color=C["primary"], opacity=0.5)
    fig.update_layout(barmode="relative", height=400,
                      margin=dict(l=0, r=0, t=10, b=0),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      hovermode="x unified")
    fig.update_yaxes(title_text="NTD", secondary_y=False)
    fig.update_yaxes(title_text="毛利率 %", secondary_y=True, range=[0, 50], showgrid=False)
    return fig


def chart_cumulative_ytd(rev_24):
    cum_2024, cum_2025 = [], []
    s24, s25 = 0, 0
    for i in range(12):
        s24 += rev_24[i]; cum_2024.append(s24)
        s25 += rev_24[i + 12]; cum_2025.append(s25)
    labels = [f"{i}月" for i in range(1, 13)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(name="2024 累計", x=labels, y=cum_2024, mode="lines+markers",
                            line=dict(color=C["neutral"], width=2),
                            hovertemplate="2024 %{x}<br>累計：NT$ %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(name="2025 累計", x=labels, y=cum_2025, mode="lines+markers",
                            line=dict(color=C["primary"], width=3),
                            fill="tonexty", fillcolor="rgba(37,99,235,0.08)",
                            hovertemplate="2025 %{x}<br>累計：NT$ %{y:,.0f}<extra></extra>"))
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      hovermode="x unified", yaxis_title="累計營業額 (NTD)")
    return fig


def chart_est_vs_act_gp(months, est_gp, act_gp, est_gm, act_gm):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(name="EST 毛利", x=months, y=est_gp, marker_color=C["blue_l"],
                        hovertemplate="%{x}<br>EST GP：NT$ %{y:,.0f}<extra></extra>"))
    # Only show ACT bars where data exists (non-zero)
    act_show = [v if v > 0 else None for v in act_gp]
    fig.add_trace(go.Bar(name="ACT 毛利", x=months, y=act_show, marker_color=C["success"],
                        hovertemplate="%{x}<br>ACT GP：NT$ %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(name="EST GM%", x=months, y=est_gm, mode="lines",
                            line=dict(color=C["primary"], width=2, dash="dot"),
                            hovertemplate="EST GM：%{y:.1f}%<extra></extra>"), secondary_y=True)
    act_gm_show = [v if v > 0 else None for v in act_gm]
    fig.add_trace(go.Scatter(name="ACT GM%", x=months, y=act_gm_show, mode="lines+markers",
                            line=dict(color=C["danger"], width=2),
                            hovertemplate="ACT GM：%{y:.1f}%<extra></extra>"), secondary_y=True)
    fig.update_layout(barmode="group", height=380,
                      margin=dict(l=0, r=0, t=10, b=0),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      hovermode="x unified")
    fig.update_yaxes(title_text="毛利 (NTD)", secondary_y=False)
    fig.update_yaxes(title_text="毛利率 %", secondary_y=True, range=[0, 50], showgrid=False)
    return fig


def chart_opex_trend(months, opex, rolling_3m):
    fig = go.Figure()
    fig.add_trace(go.Bar(name="月度 OPEX", x=months, y=opex, marker_color=C["orange_l"],
                        hovertemplate="%{x}<br>OPEX：NT$ %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(name="3 個月滾動平均", x=months, y=rolling_3m, mode="lines+markers",
                            line=dict(color=C["danger"], width=2.5),
                            hovertemplate="3M avg：NT$ %{y:,.0f}<extra></extra>"))
    fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      hovermode="x unified", yaxis_title="NTD")
    return fig


def chart_opex_categories(months, salary, software, marketing, rent, transport):
    fig = go.Figure()
    cats = [
        ("薪資", salary, C["primary"]),
        ("廣告行銷", marketing, C["danger"]),
        ("軟體服務", software, C["success"]),
        ("租金", rent, C["warning"]),
        ("交通", transport, C["purple"]),
    ]
    for name, data, color in cats:
        fig.add_trace(go.Scatter(name=name, x=months, y=data, mode="lines+markers",
                                line=dict(color=color, width=2),
                                hovertemplate=f"{name}：NT$ %{{y:,.0f}}<extra></extra>"))
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      hovermode="x unified", yaxis_title="NTD")
    return fig


def chart_opex_pct_revenue(months, opex_pct):
    fig = go.Figure()
    fig.add_trace(go.Scatter(name="OPEX 佔營收 %", x=months, y=opex_pct, mode="lines+markers",
                            line=dict(color=C["warning"], width=3),
                            fill="tozeroy", fillcolor="rgba(234,88,12,0.1)",
                            hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>"))
    fig.add_hline(y=50, line_dash="dash", line_color=C["danger"], annotation_text="50% 警戒線")
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                      hovermode="x unified", yaxis_title="OPEX / Revenue %")
    return fig


def chart_cogs_composition(vendor, tappay, guolian):
    """最新月 COGS 組成圓餅"""
    fig = go.Figure(data=[go.Pie(
        labels=["供應商成本", "TapPay 手續費", "國聯手續費"],
        values=[vendor, tappay, guolian],
        hole=0.5,
        marker=dict(colors=[C["primary"], C["warning"], C["success"]]),
        hovertemplate="%{label}<br>NT$ %{value:,.0f} (%{percent})<extra></extra>",
    )])
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                      legend=dict(orientation="h"))
    return fig


def chart_ar_collection(ar_buckets, current_month="2025-12"):
    """未來 AR 收款預期"""
    fig = go.Figure()
    months = [b["month"] for b in ar_buckets if b["month"] != "#N/A"]
    amounts = [b["amount"] for b in ar_buckets if b["month"] != "#N/A"]
    counts = [b["count"] for b in ar_buckets if b["month"] != "#N/A"]
    colors = [C["danger"] if m <= current_month else C["success"] for m in months]
    text_labels = [f"{c} 筆<br>NT$ {a/10000:.0f} 萬" for c, a in zip(counts, amounts)]
    fig.add_trace(go.Bar(x=months, y=amounts, marker_color=colors,
                        text=text_labels, textposition="outside",
                        hovertemplate="%{x}<br>金額：NT$ %{y:,.0f}<br>訂單：%{customdata} 筆<extra></extra>",
                        customdata=counts))
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=30, b=0),
                      showlegend=False,
                      xaxis_title="預期收款月份",
                      yaxis_title="應收金額 (NTD)")
    return fig


def chart_gm_by_product(products):
    """Top 10 產品 GM% horizontal bar"""
    products_sorted = sorted(products, key=lambda x: x["gm_avg"], reverse=True)[:10]
    labels = [p["product"] for p in products_sorted]
    gms = [p["gm_avg"] for p in products_sorted]
    sales = [p["sales_total"] / 10000 for p in products_sorted]
    fig = go.Figure()
    colors_bar = [C["success"] if g >= 30 else (C["warning"] if g >= 20 else C["danger"]) for g in gms]
    fig.add_trace(go.Bar(
        x=gms, y=labels, orientation="h",
        marker_color=colors_bar,
        text=[f"{g:.1f}% · 銷售 {s:.0f} 萬" for g, s in zip(gms, sales)],
        textposition="outside",
        hovertemplate="%{y}<br>GM：%{x:.1f}%<br>累計銷售：%{customdata:,.0f} 萬<extra></extra>",
        customdata=sales,
    ))
    fig.update_layout(height=480, margin=dict(l=0, r=80, t=20, b=10),
                      xaxis_title="平均毛利率 %", yaxis=dict(autorange="reversed"))
    return fig


def chart_pivot_sales(months_pivot, sales, gp, gm):
    """Pivot Table 23-month Sales/GP/GM% trend"""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(name="總營收 (含預訂)", x=months_pivot, y=sales,
                        marker_color=C["blue_l"]))
    fig.add_trace(go.Bar(name="毛利", x=months_pivot, y=gp,
                        marker_color=C["green_l"]))
    fig.add_trace(go.Scatter(name="毛利率 %", x=months_pivot, y=gm, mode="lines+markers",
                            line=dict(color=C["danger"], width=2.5)), secondary_y=True)
    fig.update_layout(barmode="group", height=380,
                      margin=dict(l=0, r=0, t=10, b=0),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      hovermode="x unified")
    fig.update_yaxes(title_text="NTD", secondary_y=False)
    fig.update_yaxes(title_text="毛利率 %", secondary_y=True, range=[0, 50], rangemode="tozero")
    return fig
