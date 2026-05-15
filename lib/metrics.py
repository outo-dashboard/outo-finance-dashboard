"""metrics.py - 計算真實資料的指標"""


def compute_metrics(data, month_idx=None):
    months = data["months_24"]
    d = data["dashboard"]
    idx = month_idx if month_idx is not None else len(months) - 1
    idx = max(0, min(idx, len(months) - 1))

    rev = d["revenue"]
    cogs = d["cogs_total"]
    gp = d["est_gross_profit"]
    gm = d["est_gross_margin"]
    act_gp = d["act_gross_profit"]
    act_gm = d["act_gross_margin"]
    opex = d["opex_total"]
    ebit = [g - o for g, o in zip(gp, opex)]

    ytd_2024 = sum(rev[0:12])
    ytd_2025 = sum(rev[12:24])
    avg_opex_12m = sum(opex[-12:]) / 12
    avg_revenue_12m = sum(rev[-12:]) / 12
    avg_gm_12m = sum(gm[-12:]) / 12

    mom = ((rev[idx] - rev[idx-1]) / rev[idx-1] * 100) if idx > 0 and rev[idx-1] else 0
    yoy = ((rev[idx] - rev[idx-12]) / rev[idx-12] * 100) if idx >= 12 and rev[idx-12] else 0

    rolling_3m = [sum(opex[max(0, i-2):i+1]) / min(3, i+1) for i in range(len(opex))]
    rev_rolling_3m = [sum(rev[max(0, i-2):i+1]) / min(3, i+1) for i in range(len(rev))]
    opex_pct = [(opex[i] / rev[i] * 100) if rev[i] else 0 for i in range(len(rev))]

    return {
        "months": months,
        "idx": idx,
        "rev": rev, "cogs": cogs, "gp": gp, "gm": gm,
        "act_gp": act_gp, "act_gm": act_gm,
        "opex": opex, "ebit": ebit,
        "rolling_3m_opex": rolling_3m,
        "rolling_3m_rev": rev_rolling_3m,
        "opex_pct_rev": opex_pct,
        "vendor_estimated": d["vendor_cost_estimated"],
        "vendor_actual": d["vendor_cost_actual"],
        "tappay_fees": d["tappay_fees"],
        "guolian_fees": d["guolian_fees"],
        "salary": d["salary"],
        "software": d["software"],
        "marketing": d["marketing"],
        "rent": d["rent"],
        "transport": d["transport"],
        "kpi": {
            "rev_latest": rev[idx],
            "gp_latest": gp[idx],
            "gm_latest": gm[idx],
            "opex_latest": opex[idx],
            "ebit_latest": ebit[idx],
            "act_gp_latest": act_gp[idx],
            "act_gm_latest": act_gm[idx],
            "mom_pct": mom,
            "yoy_pct": yoy,
            "ytd_2024": ytd_2024,
            "ytd_2025": ytd_2025,
            "ytd_yoy": ((ytd_2025/ytd_2024 - 1) * 100) if ytd_2024 else 0,
            "avg_opex_12m": avg_opex_12m,
            "avg_revenue_12m": avg_revenue_12m,
            "avg_gm_12m": avg_gm_12m,
            "ebit_avg_12m": sum(ebit[-12:]) / 12,
        }
    }
