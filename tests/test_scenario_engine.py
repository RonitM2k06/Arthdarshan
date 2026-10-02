import copy
import json
from pathlib import Path

import pytest

from ai.misconception.taxonomy import MISCONCEPTION_IDS
from ai.scenario_engine import engine as eng
from ai.scenario_engine.schema import DIMENSIONS, Scenario
from apps.api.services.content import concept_ids

SCEN_DIR = Path(__file__).resolve().parents[1] / "configs" / "scenarios"
IDS = sorted(p.stem for p in SCEN_DIR.glob("*.json"))


def test_eight_scenarios_exist(scenarios):
    assert len(scenarios) >= 8
    for sid in ["guaranteed_opportunity", "whatsapp_expert", "market_shock", "one_basket", "hidden_fee",
                "urgent_decision", "confusing_document", "family_file"]:
        assert sid in scenarios


@pytest.mark.parametrize("sid", IDS)
def test_scenario_valid(sid, scenarios):
    sc = scenarios[sid]
    errs = eng.validate_scenario(sc, known_concepts=concept_ids(), known_misconceptions=set(MISCONCEPTION_IDS))
    assert errs == []
    assert "NO REAL MONEY" in sc.disclaimer


@pytest.mark.parametrize("sid", IDS)
def test_every_transition_executes(sid, scenarios):
    """Walk every (state, action) edge: the engine must produce a legal next state."""
    sc = scenarios[sid]
    edges = 0
    for key, st in sc.states.items():
        for a in st.actions:
            res = eng.step(sc, key, a.id, [])
            assert res.next_state_key in sc.states
            assert res.quality in ("safe", "mixed", "unsafe")
            edges += 1
    assert edges >= 8


@pytest.mark.parametrize("sid", IDS)
def test_each_scenario_has_a_safe_ending(sid, scenarios):
    kinds = {s.outcome.kind for s in scenarios[sid].states.values() if s.terminal}
    assert "safe" in kinds
    assert len(kinds) >= 2


def test_hero_branching(scenarios):
    sc = scenarios["guaranteed_opportunity"]
    r = eng.step(sc, "s1_message", "invest")
    assert r.next_state_key == "s2_fee" and r.quality == "unsafe"
    assert "M001" in r.misconception_signals
    assert eng.step(sc, "s1_message", "verify").next_state_key == "s3_regclaim"
    assert eng.step(sc, "s1_message", "investigate").next_state_key == "s6_investigation"
    assert eng.step(sc, "s1_message", "walk").terminal is True
    assert "₹2,000 verification fee" in " ".join(sc.states["s2_fee"].channel.messages)


def test_no_actions_after_terminal(scenarios):
    sc = scenarios["guaranteed_opportunity"]
    with pytest.raises(eng.InvalidAction):
        eng.step(sc, "t_walk", "anything")


def test_invalid_action_and_state(scenarios):
    sc = scenarios["guaranteed_opportunity"]
    with pytest.raises(eng.InvalidAction):
        eng.step(sc, "s1_message", "nonexistent")
    with pytest.raises(eng.InvalidState):
        eng.step(sc, "no_such_state", "invest")


def test_determinism(scenarios):
    sc = scenarios["market_shock"]
    a = eng.step(sc, "m1_shock", "pause_plan", ["ms_panic"])
    b = eng.step(sc, "m1_shock", "pause_plan", ["ms_panic"])
    assert a == b


def test_evidence_recall(scenarios):
    sc = scenarios["guaranteed_opportunity"]
    st = sc.states["s1_message"]
    r = eng.evidence_recall(st, ["e_guar", "e_urgent", "e_tone", "bogus_id"])
    assert set(r.noticed_red_flags) == {"e_guar", "e_urgent"}
    assert "e_auth" in r.missed_red_flags
    assert r.false_alarms == ["e_tone"]
    assert 0 < r.recall < 1
    assert eng.evidence_recall(st, []).recall == 0
    assert eng.evidence_recall(sc.states["t_walk"], []).recall is None


def test_public_view_hides_answer_key(scenarios):
    sc = scenarios["guaranteed_opportunity"]
    view = eng.public_state_view(sc, "s1_message")
    blob = json.dumps(view)
    assert '"kind"' not in blob and '"why"' not in blob and "quality" not in blob
    assert all(set(e) == {"id", "label", "text"} for e in view["evidence"])


def _mutated(scenarios, fn):
    d = copy.deepcopy(scenarios["guaranteed_opportunity"].model_dump())
    fn(d)
    return Scenario.model_validate(d)


def test_validator_catches_dangling_transition(scenarios):
    sc = _mutated(scenarios, lambda d: d["states"]["s1_message"]["actions"][0].update(next="nowhere"))
    assert any("does not exist" in e for e in eng.validate_scenario(sc))


def test_validator_catches_unreachable_and_deadend(scenarios):
    def mut(d):
        d["states"]["orphan"] = copy.deepcopy(d["states"]["s6_investigation"]) | {"id": "orphan"}
    assert any("unreachable" in e for e in eng.validate_scenario(_mutated(scenarios, mut)))

    def loop(d):
        d["states"]["s6_investigation"]["actions"] = [
            {**a, "next": "s6_investigation"} for a in d["states"]["s6_investigation"]["actions"]]
    assert any("cannot reach any terminal" in e for e in eng.validate_scenario(_mutated(scenarios, loop)))


def test_validator_requires_terminal_outcome_and_safe_action(scenarios):
    def mut(d):
        d["states"]["t_walk"]["outcome"] = None
    assert any("needs an outcome" in e for e in eng.validate_scenario(_mutated(scenarios, mut)))

    def mut2(d):
        for a in d["states"]["s1_message"]["actions"]:
            a["quality"] = "unsafe"
    assert any("no action with quality 'safe'" in e for e in eng.validate_scenario(_mutated(scenarios, mut2)))


def test_validator_blocks_credential_requests_and_advice(scenarios):
    def mut(d):
        d["states"]["s1_message"]["channel"]["messages"].append("Please share your OTP to continue")
    assert any("sensitive" in e for e in eng.validate_scenario(_mutated(scenarios, mut)))

    def mut2(d):
        d["states"]["s1_message"]["narrative"] += " You should buy this stock."
    assert any("advice" in e for e in eng.validate_scenario(_mutated(scenarios, mut2)))


def test_schema_rejects_bad_fields(scenarios):
    d = copy.deepcopy(scenarios["guaranteed_opportunity"].model_dump())
    d["states"]["s1_message"]["pressure"][0]["type"] = "telepathy"
    with pytest.raises(Exception):
        Scenario.model_validate(d)
    d = copy.deepcopy(scenarios["guaranteed_opportunity"].model_dump())
    d["unexpected"] = 1
    with pytest.raises(Exception):
        Scenario.model_validate(d)


def test_localization_overlay(scenarios):
    sc = scenarios["guaranteed_opportunity"]
    hing = eng.localize(sc, "hinglish")
    assert hing.states["s1_message"].actions[0].label != sc.states["s1_message"].actions[0].label
    hi = eng.localize(sc, "hi")
    assert "राहुल" in hi.states["s1_message"].narrative
    assert eng.localize(sc, "xx") is sc
    assert [a.id for a in hing.states["s1_message"].actions] == [a.id for a in sc.states["s1_message"].actions]
    assert hing.states["s1_message"].actions[0].quality == "unsafe"


def test_pressure_recorded(scenarios):
    sc = scenarios["urgent_decision"]
    r = eng.step(sc, "u1_timer", "pause")
    assert r.countdown_seconds == 30
    assert {"countdown", "social_proof", "peer_pressure", "fomo"} <= set(r.pressure_types)
    assert set(DIMENSIONS) >= set(sc.scoring.dimensions)


def test_all_pressure_types_used_somewhere(scenarios):
    used = {p.type for s in scenarios.values() for st in s.states.values() for p in st.pressure}
    for t in ["urgency", "countdown", "scarcity", "social_proof", "authority", "fomo", "fear", "greed",
              "loss_recovery", "peer_pressure"]:
        assert t in used, t


def test_hindi_falls_back_to_hinglish_not_english(scenarios):
    sc = scenarios["market_shock"]                       # has Hinglish overlay only
    hi = eng.localize(sc, "hi")
    assert hi.states["m1_shock"].title == eng.localize(sc, "hinglish").states["m1_shock"].title != sc.states["m1_shock"].title
    hero = eng.localize(scenarios["guaranteed_opportunity"], "hi")     # full Devanagari where translated
    assert any("ऀ" <= c <= "ॿ" for c in hero.states["s1_message"].title)
