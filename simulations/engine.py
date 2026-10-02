"""Consequence simulations. Pure, deterministic (seeded) functions. NO REAL MONEY. NOTHING HERE IS A FORECAST.

Every result carries `label` = ILLUSTRATIVE · SIMULATED · NO REAL MONEY and plain-language `insights`
that teach a concept; none gives a recommendation.
"""
from __future__ import annotations

import math
from typing import Any, Callable

import numpy as np

LABEL = "ILLUSTRATIVE · SIMULATED · NO REAL MONEY"


class SimulationError(ValueError):
    pass


def P(key: str, label: str, lo: float, hi: float, default: float, step: float = 1, unit: str = "", hint: str = "") -> dict:
    return {"key": key, "label": label, "min": lo, "max": hi, "default": default, "step": step, "unit": unit, "hint": hint}


def _clean(params: dict[str, Any], spec: list[dict]) -> dict[str, float]:
    out: dict[str, float] = {}
    for s in spec:
        v = params.get(s["key"], s["default"])
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise SimulationError(f"{s['key']} must be a finite number")
        if v < s["min"] or v > s["max"]:
            raise SimulationError(f"{s['key']} must be between {s['min']} and {s['max']}")
        out[s["key"]] = float(v)
    unknown = set(params) - {s["key"] for s in spec}
    if unknown:
        raise SimulationError(f"unknown parameter(s): {', '.join(sorted(unknown))}")
    return out


def inr(x: float) -> str:
    return f"₹{x:,.0f}"


# ------------------------------------------------------------------------------------------------
def fee_erosion(p: dict) -> dict:
    amt, yrs, g, fee, entry = p["amount"], int(p["years"]), p["growth"] / 100, p["fee"] / 100, p["entry_fee"] / 100
    gross = [amt]
    net = [amt * (1 - entry)]
    for _ in range(yrs):
        gross.append(gross[-1] * (1 + g))
        net.append(net[-1] * (1 + g) * (1 - fee))
    lost = gross[-1] - net[-1]
    share = lost / (gross[-1] - amt) * 100 if gross[-1] > amt else None
    insights = [f"With the same hypothetical growth, charges alone change the end amount from {inr(gross[-1])} to {inr(net[-1])}."]
    if share is not None:
        insights.append(f"Charges consumed about {share:.0f}% of the hypothetical growth.")
    insights.append("A yearly charge is taken from a balance that is supposed to be growing, so it compounds against you.")
    insights.append("Growth here is an assumption, not a forecast. Real results vary and can be negative, but charges apply either way.")
    return {"series": [{"name": "Without charges", "points": gross}, {"name": "After charges", "points": net}],
            "x_label": "Year", "y_label": "Illustrative amount (₹)",
            "summary": {"final_gross": round(gross[-1]), "final_net": round(net[-1]), "lost_to_charges": round(lost),
                        "share_of_growth_lost_pct": None if share is None else round(share, 1)}, "insights": insights}


def compounding(p: dict) -> dict:
    amt, yrs, r, add = p["amount"], int(p["years"]), p["rate"] / 100, p["monthly_add"]
    comp, simple, contrib = [amt], [amt], [amt]
    v = amt
    for y in range(1, yrs + 1):
        for _ in range(12):
            v = v * (1 + r / 12) + add
        comp.append(v)
        contrib.append(amt + add * 12 * y)
        simple.append(amt + amt * r * y + add * 12 * y)
    growth_part = comp[-1] - contrib[-1]
    insights = [f"Of the {inr(comp[-1])} at the end, {inr(contrib[-1])} is money put in and {inr(growth_part)} is hypothetical growth.",
                f"Growing on earlier growth (compounding) gives {inr(comp[-1] - simple[-1])} more than growing only on the original amount.",
                "Time does most of the work, which is why starting early matters — and why costs and debts compound against you too.",
                "The rate is hypothetical. This is not a forecast and no return is guaranteed."]
    return {"series": [{"name": "With compounding", "points": comp}, {"name": "Without compounding", "points": simple},
                       {"name": "Money put in", "points": contrib}], "x_label": "Year", "y_label": "Illustrative amount (₹)",
            "summary": {"final": round(comp[-1]), "contributed": round(contrib[-1]), "growth": round(growth_part)}, "insights": insights}


def inflation(p: dict) -> dict:
    amt, yrs, inf, sav = p["amount"], int(p["years"]), p["inflation"] / 100, p["savings_rate"] / 100
    nominal = [amt * (1 + sav) ** y for y in range(yrs + 1)]
    real = [nominal[y] / (1 + inf) ** y for y in range(yrs + 1)]
    basket = [amt * (1 + inf) ** y for y in range(yrs + 1)]
    gap = real[-1] - amt
    insights = [f"After {yrs} years, {inr(amt)} of today's goods would cost about {inr(basket[-1])} at {p['inflation']:.1f}% a year (illustrative).",
                f"Your money grows to {inr(nominal[-1])} in rupee terms, but in today's buying power that is about {inr(real[-1])}.",
                ("Buying power rose a little." if gap > 0 else "Buying power fell even though the rupee number rose.") if sav > 0 else "With no growth, buying power falls every year.",
                "Inflation is why 'safe' and 'growing' are different questions. Rates here are hypothetical."]
    return {"series": [{"name": "Rupee amount", "points": nominal}, {"name": "Buying power (today's rupees)", "points": real},
                       {"name": "Cost of the same goods", "points": basket}], "x_label": "Year", "y_label": "Illustrative amount (₹)",
            "summary": {"nominal": round(nominal[-1]), "real": round(real[-1]), "basket_cost": round(basket[-1])}, "insights": insights}


def concentration(p: dict) -> dict:
    total, conc, shock = p["amount"], p["share_in_one"] / 100, p["shock"] / 100
    loss = total * conc * shock
    levels = list(range(0, 101, 10))
    bars = [{"label": f"{l}%", "value": round(total * (l / 100) * shock)} for l in levels]
    insights = [f"With {p['share_in_one']:.0f}% of the money in one asset, a {p['shock']:.0f}% fall in that asset costs {inr(loss)} — {conc * shock * 100:.1f}% of the total.",
                f"If that asset were only 10% of the money, the same event would cost {inr(total * 0.1 * shock)}.",
                "Concentration risk is the share of your money exposed to a single event. Reducing it limits how much one bad event can hurt.",
                "This shows one asset failing. It says nothing about market-wide falls (see the Diversification simulation)."]
    return {"series": [], "bars": bars, "x_label": "Share of money in the one asset", "y_label": "Illustrative loss (₹)",
            "summary": {"loss": round(loss), "remaining": round(total - loss), "loss_pct_of_total": round(conc * shock * 100, 1)}, "insights": insights}


def diversification(p: dict) -> dict:
    sigma, rho, maxn = p["asset_volatility"], p["correlation"], int(p["max_assets"])
    pts = [sigma * math.sqrt(1 / n + (1 - 1 / n) * rho) for n in range(1, maxn + 1)]
    floor = sigma * math.sqrt(rho)
    insights = [f"One asset has illustrative volatility {sigma:.0f}%. Spreading equally across {maxn} similar-risk assets brings it down to about {pts[-1]:.1f}%.",
                f"It cannot go below about {floor:.1f}% here, because the assets move together (correlation {rho:.2f}). That floor is market-wide risk.",
                "Diversification reduces concentration risk but does not remove risk. Two very similar assets (correlation near 1) hardly help.",
                "Volatility here is a measure of swings, not a prediction of losses."]
    return {"series": [{"name": "Portfolio volatility %", "points": pts}, {"name": "Floor from market-wide risk %", "points": [floor] * len(pts)}],
            "x_label": "Number of assets (index 1 = a single asset)", "y_label": "Illustrative volatility (%)",
            "summary": {"single_asset_vol": sigma, "diversified_vol": round(pts[-1], 2), "floor": round(floor, 2),
                        "risk_removed_pct": round((1 - pts[-1] / sigma) * 100, 1) if sigma else 0}, "insights": insights}


def volatility(p: dict) -> dict:
    vol, drift, yrs, seed = p["volatility"] / 100, p["drift"] / 100, int(p["years"]), int(p["seed"])
    rng = np.random.default_rng(seed)
    steps = yrs * 12
    paths = []
    for _ in range(5):
        z = rng.standard_normal(steps)
        r = (drift - 0.5 * vol ** 2) / 12 + vol / math.sqrt(12) * z
        paths.append(100 * np.exp(np.concatenate([[0], np.cumsum(r)])))
    series = [{"name": f"Fictional path {i + 1}", "points": [round(float(x), 2) for x in path]} for i, path in enumerate(paths)]
    dd = []
    for path in paths:
        peak = np.maximum.accumulate(path)
        dd.append(float(((path - peak) / peak).min()))
    finals = [float(pp[-1]) for pp in paths]
    insights = [f"Five fictional paths start at 100 and end between {min(finals):.0f} and {max(finals):.0f} — same settings, different roads.",
                f"The deepest fall from a previous peak ranged from {abs(max(dd)) * 100:.0f}% to {abs(min(dd)) * 100:.0f}%.",
                "Higher volatility means a wider spread of paths and bigger swings along the way. It does not say which direction prices will go.",
                "These paths are random fictional examples. They are not predictions and the numbers are not real."]
    return {"series": series, "x_label": "Month", "y_label": "Fictional value (start = 100)",
            "summary": {"min_final": round(min(finals), 1), "max_final": round(max(finals), 1), "worst_drawdown_pct": round(abs(min(dd)) * 100, 1)},
            "insights": insights}


def liquidity(p: dict) -> dict:
    need, month = p["need_amount"], int(p["need_month"])
    lock, load, pen = int(p["lockin_months"]), p["exit_load"] / 100, p["early_penalty"] / 100
    options = [
        {"name": "Easy-access savings", "received": need, "cost": 0.0, "note": "Available immediately at no charge."},
        {"name": f"Deposit locked for {lock} months", "received": need * (1 - (pen if month < lock else 0)),
         "cost": need * (pen if month < lock else 0), "note": "Early withdrawal penalty applies before the lock ends." if month < lock else "Lock-in has ended."},
        {"name": "Scheme with exit charge", "received": need * (1 - (load if month < 12 else 0)),
         "cost": need * (load if month < 12 else 0), "note": "Exit charge applies in the first 12 months." if month < 12 else "Exit charge no longer applies."},
        {"name": "Scheme that blocks withdrawals", "received": 0.0, "cost": need, "note": "Cannot access the money at all — a serious warning sign."},
    ]
    insights = [f"Needing {inr(need)} in month {month}: the cost of access ranges from {inr(0)} to {inr(need)} depending on liquidity.",
                "Liquidity is how quickly and cheaply you can turn something into cash. It matters most exactly when you need money unexpectedly.",
                "A product that delays withdrawals or charges 'fees to release your money' deserves extra caution."]
    return {"series": [], "bars": [{"label": o["name"], "value": round(o["received"]), "extra": o} for o in options],
            "x_label": "Option", "y_label": "Amount you actually receive (₹)", "options": options,
            "summary": {"need": need, "month": month}, "insights": insights}


def emergency_savings(p: dict) -> dict:
    exp, fund_m, loss_m, rate = p["monthly_expense"], p["fund_months"], int(p["income_loss_months"]), p["borrow_rate"] / 100
    balance = exp * fund_m
    pts, borrowed = [balance], 0.0
    for _ in range(loss_m):
        balance -= exp
        if balance < 0:
            borrowed += -balance
            balance = 0
        pts.append(balance - borrowed)
    interest = borrowed * rate * (loss_m / 12)
    insights = [f"A cushion of {fund_m:.0f} months covers {fund_m:.0f} months of expenses; the simulated income gap lasts {loss_m} months.",
                ("The cushion covers the whole gap." if borrowed == 0 else f"{inr(borrowed)} had to be borrowed or taken from investments in a hurry (illustrative interest {inr(interest)})."),
                "An emergency cushion's job is safety and access, not return. It reduces forced decisions at bad moments."]
    return {"series": [{"name": "Balance (negative = borrowed)", "points": pts}], "x_label": "Month of income gap", "y_label": "Illustrative balance (₹)",
            "summary": {"borrowed": round(borrowed), "interest": round(interest), "covered": borrowed == 0}, "insights": insights}


def scam_loss(p: dict) -> dict:
    first, factor, rounds, stop = p["first_payment"], p["escalation"], int(p["rounds"]), int(p["stop_round"])
    stop = min(stop, rounds)
    pays = [first * factor ** i for i in range(rounds)]
    cum = np.cumsum(pays)
    bars = [{"label": f"Round {i + 1}", "value": round(float(c)), "extra": {"payment": round(pays[i])}} for i, c in enumerate(cum)]
    lost_at_stop = float(cum[stop - 1])
    insights = [f"The first request is {inr(first)}. Each new 'step' asks {factor:.1f}× the last, with a new reason to pay.",
                f"If you stop at round {stop}, the simulated loss is {inr(lost_at_stop)}; continuing to round {rounds} would reach {inr(float(cum[-1]))}.",
                f"Stopping at round 1 instead would have cost {inr(pays[0])}. The earliest checkpoint — before paying — costs nothing.",
                "Scams escalate because each payment makes stopping feel like losing what you have already paid (the sunk-cost trap)."]
    return {"series": [{"name": "Cumulative simulated loss", "points": [0.0] + [float(c) for c in cum]}], "bars": bars,
            "x_label": "Round of payment", "y_label": "Illustrative cumulative loss (₹)",
            "summary": {"lost_at_stop": round(lost_at_stop), "if_continued": round(float(cum[-1])), "first_payment": round(first)}, "insights": insights}


REGISTRY: dict[str, dict] = {
    "fee_erosion": {"name": "Fee erosion", "concepts": ["fees", "compounding"], "fn": fee_erosion, "params": [
        P("amount", "Starting amount", 1000, 1_000_000, 10000, 1000, "₹"), P("years", "Years", 1, 40, 5, 1, "yrs"),
        P("growth", "Hypothetical growth per year", 0, 15, 8, 0.5, "%", "An assumption, not a forecast"),
        P("fee", "Yearly charge", 0, 5, 2, 0.1, "%"), P("entry_fee", "Entry charge", 0, 5, 0, 0.5, "%")],
        "blurb": "See how charges that look small can change the end amount."},
    "compounding": {"name": "Compounding", "concepts": ["compounding", "sip"], "fn": compounding, "params": [
        P("amount", "Starting amount", 0, 1_000_000, 10000, 1000, "₹"), P("monthly_add", "Added every month", 0, 100000, 0, 500, "₹"),
        P("years", "Years", 1, 40, 10, 1, "yrs"), P("rate", "Hypothetical growth per year", 0, 15, 8, 0.5, "%")],
        "blurb": "Growth on growth: what time does when nothing else changes."},
    "inflation": {"name": "Inflation", "concepts": ["inflation", "saving"], "fn": inflation, "params": [
        P("amount", "Amount today", 1000, 1_000_000, 100000, 1000, "₹"), P("years", "Years", 1, 40, 10, 1, "yrs"),
        P("inflation", "Illustrative inflation per year", 0, 12, 6, 0.5, "%"), P("savings_rate", "Illustrative growth per year", 0, 12, 4, 0.5, "%")],
        "blurb": "Why the same rupees buy less later."},
    "concentration": {"name": "Concentration risk", "concepts": ["concentration_risk", "diversification"], "fn": concentration, "params": [
        P("amount", "Total (fictional)", 1000, 1_000_000, 50000, 1000, "₹"), P("share_in_one", "Share in a single asset", 0, 100, 100, 5, "%"),
        P("shock", "Fall in that asset", 0, 90, 35, 5, "%")],
        "blurb": "How much one bad event can take, depending on how much depended on it."},
    "diversification": {"name": "Diversification", "concepts": ["diversification", "risk"], "fn": diversification, "params": [
        P("asset_volatility", "Swings of one asset", 5, 60, 25, 1, "%"), P("correlation", "How much assets move together", 0, 1, 0.4, 0.05, ""),
        P("max_assets", "Number of assets", 1, 30, 10, 1, "")],
        "blurb": "What spreading across assets can — and cannot — do."},
    "volatility": {"name": "Volatility", "concepts": ["volatility", "risk"], "fn": volatility, "params": [
        P("volatility", "Yearly swings", 2, 60, 20, 1, "%"), P("drift", "Hypothetical average growth", -10, 20, 6, 1, "%"),
        P("years", "Years", 1, 20, 5, 1, "yrs"), P("seed", "Random seed (change for new paths)", 0, 9999, 7, 1, "")],
        "blurb": "Fictional paths with the same settings, different roads."},
    "liquidity": {"name": "Liquidity", "concepts": ["liquidity", "fees"], "fn": liquidity, "params": [
        P("need_amount", "Money you suddenly need", 1000, 1_000_000, 20000, 1000, "₹"), P("need_month", "Month you need it", 1, 60, 6, 1, "mo"),
        P("lockin_months", "Deposit lock-in", 1, 60, 24, 1, "mo"), P("exit_load", "Scheme exit charge", 0, 5, 1, 0.5, "%"),
        P("early_penalty", "Early withdrawal penalty", 0, 10, 2, 0.5, "%")],
        "blurb": "The cost of needing your money early."},
    "emergency_savings": {"name": "Emergency savings", "concepts": ["saving", "liquidity"], "fn": emergency_savings, "params": [
        P("monthly_expense", "Monthly expenses", 1000, 200000, 20000, 1000, "₹"), P("fund_months", "Cushion (months of expenses)", 0, 12, 3, 1, "mo"),
        P("income_loss_months", "Months without income", 1, 12, 4, 1, "mo"), P("borrow_rate", "Borrowing cost per year", 0, 36, 18, 1, "%")],
        "blurb": "What a cushion buys you when income stops."},
    "scam_loss": {"name": "Scam loss progression", "concepts": ["fraud_red_flags", "risk"], "fn": scam_loss, "params": [
        P("first_payment", "First payment asked", 100, 100000, 5000, 100, "₹"), P("escalation", "Each new ask is × the last", 1, 3, 1.4, 0.1, "×"),
        P("rounds", "Number of rounds", 1, 8, 5, 1, ""), P("stop_round", "You stop at round", 1, 8, 2, 1, "")],
        "blurb": "How scams escalate, and why the first checkpoint matters most."},
}


def catalog() -> list[dict]:
    return [{"id": k, "name": v["name"], "concepts": v["concepts"], "blurb": v["blurb"], "params": v["params"], "label": LABEL}
            for k, v in REGISTRY.items()]


def run(sim_id: str, params: dict[str, Any] | None) -> dict:
    if sim_id not in REGISTRY:
        raise SimulationError(f"unknown simulation {sim_id!r}")
    spec = REGISTRY[sim_id]
    fn: Callable[[dict], dict] = spec["fn"]
    clean = _clean(params or {}, spec["params"])
    res = fn(clean)
    res.update({"id": sim_id, "name": spec["name"], "params": clean, "label": LABEL})
    return res
