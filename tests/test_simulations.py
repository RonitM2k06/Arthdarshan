import math

import pytest

from simulations import engine as sim

IDS = list(sim.REGISTRY)


def test_nine_simulations():
    assert set(IDS) == {"fee_erosion", "compounding", "inflation", "concentration", "diversification", "volatility",
                        "liquidity", "emergency_savings", "scam_loss"}


@pytest.mark.parametrize("sid", IDS)
def test_defaults_run_and_are_labelled(sid):
    r = sim.run(sid, {})
    assert "SIMULATED" in r["label"] and "NO REAL MONEY" in r["label"]
    assert r["insights"] and all(isinstance(i, str) for i in r["insights"])
    assert r["series"] or r.get("bars")
    for s in r["series"]:
        assert all(math.isfinite(x) for x in s["points"])


@pytest.mark.parametrize("sid", IDS)
def test_extremes_and_validation(sid):
    spec = sim.REGISTRY[sid]["params"]
    lo = {p["key"]: p["min"] for p in spec}
    hi = {p["key"]: p["max"] for p in spec}
    for params in (lo, hi):
        r = sim.run(sid, params)
        assert r["summary"]
    bad = {spec[0]["key"]: spec[0]["max"] + 1}
    with pytest.raises(sim.SimulationError):
        sim.run(sid, bad)
    with pytest.raises(sim.SimulationError):
        sim.run(sid, {spec[0]["key"]: float("nan")})
    with pytest.raises(sim.SimulationError):
        sim.run(sid, {spec[0]["key"]: "abc"})
    with pytest.raises(sim.SimulationError):
        sim.run(sid, {"nonsense": 1})


def test_unknown_sim():
    with pytest.raises(sim.SimulationError):
        sim.run("nope", {})


def test_fee_erosion_numbers_match_knowledge_base():
    r = sim.run("fee_erosion", {"amount": 100000, "years": 20, "growth": 8, "fee": 0, "entry_fee": 0})
    assert round(r["summary"]["final_gross"]) == 466096     # figure quoted in the concept text
    r = sim.run("fee_erosion", {"amount": 100000, "years": 20, "growth": 8, "fee": 2.5, "entry_fee": 0})
    assert r["summary"]["final_net"] < r["summary"]["final_gross"]
    assert r["summary"]["lost_to_charges"] > 0


def test_fee_zero_means_no_loss():
    r = sim.run("fee_erosion", {"fee": 0, "entry_fee": 0})
    assert r["summary"]["lost_to_charges"] == 0


def test_compounding_basic():
    r = sim.run("compounding", {"amount": 10000, "monthly_add": 0, "years": 10, "rate": 0})
    assert r["summary"]["final"] == 10000


def test_inflation_real_below_nominal():
    r = sim.run("inflation", {"amount": 100000, "years": 10, "inflation": 6, "savings_rate": 4})
    assert r["summary"]["real"] < 100000 < r["summary"]["nominal"]


def test_concentration_math():
    r = sim.run("concentration", {"amount": 50000, "share_in_one": 100, "shock": 35})
    assert r["summary"]["loss"] == 17500
    r = sim.run("concentration", {"amount": 50000, "share_in_one": 10, "shock": 40})
    assert r["summary"]["loss"] == 2000


def test_diversification_floor_exists():
    r = sim.run("diversification", {"asset_volatility": 30, "correlation": 0.5, "max_assets": 30})
    pts = r["series"][0]["points"]
    assert pts[0] == pytest.approx(30)
    assert all(a >= b for a, b in zip(pts, pts[1:]))
    assert pts[-1] > r["summary"]["floor"] > 0          # cannot reach zero
    r0 = sim.run("diversification", {"asset_volatility": 30, "correlation": 0, "max_assets": 30})
    assert r0["series"][0]["points"][-1] < r["series"][0]["points"][-1]
    r1 = sim.run("diversification", {"asset_volatility": 30, "correlation": 1, "max_assets": 30})
    assert r1["series"][0]["points"][-1] == pytest.approx(30)   # perfectly correlated assets: no benefit


def test_volatility_seeded_deterministic():
    a = sim.run("volatility", {"seed": 3})
    b = sim.run("volatility", {"seed": 3})
    c = sim.run("volatility", {"seed": 4})
    assert a["series"] == b["series"] and a["series"] != c["series"]
    assert len(a["series"]) == 5 and a["series"][0]["points"][0] == 100


def test_liquidity_blocked_scheme_gives_nothing():
    r = sim.run("liquidity", {"need_amount": 20000, "need_month": 6})
    by = {o["name"]: o for o in r["options"]}
    assert by["Easy-access savings"]["received"] == 20000
    assert by["Scheme that blocks withdrawals"]["received"] == 0
    assert by["Scheme with exit charge"]["received"] < 20000


def test_emergency_cushion_covers_or_borrows():
    assert sim.run("emergency_savings", {"fund_months": 6, "income_loss_months": 4})["summary"]["covered"] is True
    r = sim.run("emergency_savings", {"fund_months": 0, "income_loss_months": 4, "monthly_expense": 20000})
    assert r["summary"]["borrowed"] == 80000 and r["summary"]["interest"] > 0


def test_scam_progression_monotone():
    r = sim.run("scam_loss", {"first_payment": 5000, "escalation": 1.4, "rounds": 5, "stop_round": 2})
    vals = [b["value"] for b in r["bars"]]
    assert vals == sorted(vals)
    assert r["summary"]["lost_at_stop"] == round(5000 + 7000)
    assert r["summary"]["if_continued"] > r["summary"]["lost_at_stop"]


def test_no_recommendation_language_in_insights():
    banned = ["you should buy", "you should invest", "best fund", "will rise", "guaranteed to"]
    for sid in IDS:
        text = " ".join(sim.run(sid, {})["insights"]).lower()
        assert not any(b in text for b in banned)
