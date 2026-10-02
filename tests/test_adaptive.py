from ai.adaptive_learning import mastery
from ai.adaptive_learning.policy import UserState, find_weaknesses, rank_scenarios, recommend_other, target_difficulty

SAFE = {d: (75.0, 4) for d in ["concept_knowledge", "risk_recognition", "evidence_verification", "scam_awareness", "fomo_resistance",
                               "herd_resistance", "emotional_discipline", "independent_reasoning", "uncertainty_awareness", "terminology"]}


def state_with(**weak):
    scores = dict(SAFE)
    scores.update({k: (v, 5) for k, v in weak.items()})
    return UserState(dimension_scores=scores, concept_mastery={"risk": 0.5}, completed=[("guaranteed_opportunity", "safe")])


def test_bkt_monotone_and_bounded():
    p = 0.2
    for _ in range(6):
        nxt = mastery.update(p, "safe")
        assert p < nxt <= 1
        p = nxt
    assert p > 0.8
    q = 0.8
    assert mastery.update(q, "unsafe") < q + 0.15 * (1 - q) + 1e-9
    assert mastery.update(0.5, "unsafe") < mastery.update(0.5, "mixed") < mastery.update(0.5, "safe")
    for bad in (0.0, 1.0):
        assert 0 < mastery.update(bad, "safe") <= 1


def test_new_user_gets_hero_first(scenarios):
    recs = rank_scenarios(UserState(), scenarios)
    assert recs[0].id == "guaranteed_opportunity"
    assert "first" in recs[0].reasons[-1] or any("first experience" in r for r in recs[0].reasons)


def test_fomo_weakness_selects_pressure_scenarios(scenarios):
    recs = rank_scenarios(state_with(fomo_resistance=30), scenarios)
    assert recs[0].id == "urgent_decision"
    assert recs[0].weakness == "fomo_resistance"
    assert "countdown" in recs[0].rationale or any("countdown" in r for r in recs[0].reasons)


def test_fee_misconception_selects_fee_scenario(scenarios):
    st = state_with()
    st.misconceptions = {"M012": {"detections": 2, "status": "active", "clean_streak": 0}}
    recs = rank_scenarios(st, scenarios)
    assert recs[0].id == "hidden_fee"
    other = recommend_other(st)
    assert any(o.id == "fee_erosion" for o in other)


def test_diversification_misconception_selects_basket_scenario(scenarios):
    st = state_with()
    st.misconceptions = {"M004": {"detections": 2, "status": "active", "clean_streak": 0}}
    assert rank_scenarios(st, scenarios)[0].id == "one_basket"
    assert any(o.id == "diversification" for o in recommend_other(st))


def test_terminology_weakness_selects_document_and_lessons(scenarios):
    st = state_with(terminology=25)
    assert rank_scenarios(st, scenarios)[0].id == "confusing_document"
    assert any(o.kind == "lesson" for o in recommend_other(st))


def test_herd_weakness(scenarios):
    assert rank_scenarios(state_with(herd_resistance=25), scenarios)[0].id in ("whatsapp_expert", "urgent_decision", "guaranteed_opportunity")


def test_resolved_misconception_ignored():
    st = state_with()
    st.misconceptions = {"M001": {"detections": 3, "status": "resolved", "clean_streak": 3}}
    assert all(w.key != "M001" for w in find_weaknesses(st))


def test_repetition_penalised(scenarios):
    st = state_with(fomo_resistance=30)
    st.completed = [("urgent_decision", "safe"), ("urgent_decision", "safe")]
    assert rank_scenarios(st, scenarios)[0].id != "urgent_decision"


def test_difficulty_scales_with_readiness():
    low, _ = target_difficulty(UserState())
    high, _ = target_difficulty(UserState(dimension_scores={"risk_recognition": (90, 5)}, concept_mastery={"risk": 0.9}))
    assert low == 1 and high == 3


def test_every_recommendation_is_explained(scenarios):
    for r in rank_scenarios(state_with(fomo_resistance=30, terminology=40), scenarios):
        assert r.rationale and r.reasons
        d = r.to_dict()
        assert "predicted_success" in d and 0 < d["predicted_success"] < 1
