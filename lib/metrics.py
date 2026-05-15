"""
metrics.py - 計算 leadership 六大指標
"""

from typing import Dict, List, Optional

from .data_loader import ENTITY_LABELS


# 預設 AP/AR (2025-12)
DEFAULT_APAR = {
    "already_received": 4200000,
    "receivable": 2024640,
    "already_paid": 2800000,
    "payable": 1693860,
}

# OPEX breakdown 預設估算
DEFAULT_OPEX_BREAKDOWN = {
    "薪資支出": 962442,
    "租金": 121430,
    "廣告行銷": 818062,
    "產品開發": 307891,
    "保險費": 114013,
    "差旅 / 招待": 130000,
    "軟體服務 / SHOPIFY": 60000,
    "其他費用": 378147,
}


def compute_cash_by_entity(cashflow: Dict[str, list]) -> List[Dict]:
    """取每個 entity 的「Current 快照」現金（即第一個非零值）"""
    result = []
    for key, label in ENTITY_LABELS.items():
        arr = cashflow.get(key, [])
        latest = 0
        for v in arr:
            if v and v != 0:
                latest = v
                break
        result.append({"entity": label, "cash": latest, "ar": 0, "ap": 0})
    return result


def compute_all_metrics(data: Dict, target_month_idx: Optional[int] = None) -> Dict:
    """
    計算所有指標。
    target_month_idx 為 0~23（None 代表取最後一個月）
    """
    months = data["months"]
    d = data.get("dashboard", {})
    cf = data.get("cashflow", {})

    revenue = d.get("revenue", [0] * 24)
    cogs = d.get("cogs", [0] * 24)
    gp = d.get("gross_profit") or [r - c for r, c in zip(revenue, cogs)]
    gm = d.get("gross_margin") or [(p / r * 100) if r else 0 for p, r in zip(gp, revenue)]
    opex = d.get("operating_expenses", [0] * 24)
    ebit = [p - o for p, o in zip(gp, opex)]

    cash_by_entity = compute_cash_by_entity(cf)
    apar = DEFAULT_APAR.copy()

    idx = target_month_idx if target_month_idx is not None else len(months) - 1
    idx = max(0, min(idx, len(months) - 1))

    # KPI
    last_rev = revenue[idx]
    prev_rev = revenue[idx - 1] if idx > 0 else 0
    yoy_rev = revenue[idx - 12] if idx >= 12 else 0

    mom = ((last_rev - prev_rev) / prev_rev * 100) if prev_rev else 0
    yoy = ((last_rev - yoy_rev) / yoy_rev * 100) if yoy_rev else 0

    ytd_2024 = sum(revenue[0:12])
    ytd_2025 = sum(revenue[12:24])
    last3 = revenue[max(0, idx - 2):idx + 1]
    next_forecast = sum(last3) / len(last3) if last3 else 0

    # Q5 可動用資金
    total_cash = sum(e["cash"] for e in cash_by_entity)
    total_ar = sum(e["ar"] for e in cash_by_entity) + apar["receivable"]
    total_ap = sum(e["ap"] for e in cash_by_entity) + apar["payable"]
    available = total_cash + total_ar - total_ap

    # Burn rate
    avg_opex_12m = sum(opex[-12:]) / 12 if len(opex) >= 12 else 0
    rolling_3m = [
        sum(opex[max(0, i - 2):i + 1]) / min(3, i + 1) for i in range(len(opex))
    ]

    # 情境
    avg_rev_12m = sum(revenue[-12:]) / 12 if len(revenue) >= 12 else 0
    avg_gm_12m = sum(gm[-12:]) / 12 / 100 if len(gm) >= 12 else 0

    def runway_for(factor: float) -> Optional[float]:
        monthly_gp = avg_rev_12m * factor * avg_gm_12m
        net = monthly_gp - avg_opex_12m
        if net >= 0:
            return None
        return available / abs(net)

    scenarios = {
        "worst": {"factor": 0.5, "runway": runway_for(0.5)},
        "neutral": {"factor": 1.0, "runway": runway_for(1.0)},
        "best": {"factor": 1.3, "runway": runway_for(1.3)},
    }

    return {
        "months": months,
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": gp,
        "gross_margin": gm,
        "opex": opex,
        "ebit": ebit,
        "rolling_3m_opex": rolling_3m,
        "cash_by_entity": cash_by_entity,
        "apar": apar,
        "target_idx": idx,
        "target_label": months[idx],
        "kpi": {
            "last_revenue": last_rev,
            "mom_pct": mom,
            "yoy_pct": yoy,
            "ytd_2024": ytd_2024,
            "ytd_2025": ytd_2025,
            "next_forecast": next_forecast,
            "total_cash": total_cash,
            "total_ar": total_ar,
            "total_ap": total_ap,
            "available": available,
            "gross_profit": gp[idx],
            "gross_margin": gm[idx],
            "avg_opex_12m": avg_opex_12m,
            "runway_neutral": runway_for(1.0),
        },
        "scenarios": scenarios,
        "opex_breakdown": DEFAULT_OPEX_BREAKDOWN,
    }


def assess_large_expense(amount: float, m: Dict) -> Dict:
    """評估大額支出"""
    avail = m["kpi"]["available"]
    avg_opex = m["kpi"]["avg_opex_12m"]
    ratio = amount / avail if avail > 0 else float("inf")
    top_entity = max(m["cash_by_entity"], key=lambda x: x["cash"])

    if ratio < 0.2:
        level, color = "ok", "🟢"
        msg = f"**可承擔。** 支出佔可動用資金 {ratio*100:.1f}%。建議從現金最多的「{top_entity['entity']}（{top_entity['cash']/10000:.0f} 萬）」支付。"
    elif ratio < 0.5:
        level, color = "warn", "🟡"
        msg = f"**需評估。** 支出佔可動用資金 {ratio*100:.1f}%，超過 20%。執行前確認下一個月有 AR 入帳補回。"
    elif ratio < 1:
        level, color = "danger", "🟠"
        new_runway = (avail - amount) / max(avg_opex, 1)
        msg = f"**高風險。** 支出佔可動用資金 {ratio*100:.1f}%。會壓縮 runway 到 {new_runway:.1f} 個月。建議分期或借貸。"
    else:
        level, color = "danger", "🔴"
        msg = f"**無法承擔。** 差額 {(amount - avail)/10000:.0f} 萬需從借貸或下月 AR 補。"

    return {"level": level, "color": color, "ratio": ratio, "msg": msg}
