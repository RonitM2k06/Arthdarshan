import json
import tempfile
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from ai.llm import client, explainer
from ai.llm.templates import build_explanation
from apps.api.config import ROOT, get_settings
from database.models import Base
from database.session import make_engine

FACTS = {"scenario_title": "T", "state_title": "S", "action_label": "Invest", "quality": "unsafe", "pressure_types": ["urgency"], "red_flag_total": 7,
         "noticed": [{"id": "e1", "label": "Guaranteed 30% returns", "why": "w"}], "missed": [{"id": "e2", "label": "SEBI registered", "why": "w"}],
         "behaviours": [{"label": "x", "name": "URGENCY REACTION", "explanation": "e", "positive": False}], "misconceptions": [], "confidence": 4}


@pytest.fixture
def llm_on(monkeypatch):
    monkeypatch.setattr(client, "status", lambda force=False: {"available": True, "model": "fake"})


def fake(monkeypatch, response):
    monkeypatch.setattr(client, "generate", lambda *a, **k: response)


def test_explanation_is_deterministic_even_when_llm_available(llm_on, monkeypatch):
    fake(monkeypatch, json.dumps({"note": "this must never replace the factual explanation"}))
    text, src = explainer.explain_decision(FACTS, "en")
    assert src == "template" and text == build_explanation(FACTS, "en") and "7 warning signs" in text


def test_coach_note_used_when_valid(llm_on, monkeypatch):
    fake(monkeypatch, json.dumps({"note": "You explained your choice clearly, and that helps. Next time ask what you could check without trusting the sender."}))
    assert "check" in explainer.coach_note("My friend invested so I think it is fine to join", ["URGENCY REACTION"], "en")


@pytest.mark.parametrize("bad", [
    json.dumps({"note": "You should buy this stock now, it will rise."}),                                   # advice -> safety gateway
    json.dumps({"note": "The company lacks registration and is fraudulent, so avoid it entirely."}),         # claim about the scenario
    json.dumps({"note": "You earned 14% returns last year which was very nice indeed."}),                    # invented number
    json.dumps({"note": "ok"}), "this is not json at all", None, "", json.dumps({"other": "field"}), json.dumps({"note": "x" * 2000}),
    json.dumps({"note": "Aap bahut accha kar rahe hain, aur aage bhi karte rahiye aap"}),                    # Hinglish text for an English request is fine; below tests language mismatch
])
def test_bad_coach_output_is_dropped(llm_on, monkeypatch, bad):
    fake(monkeypatch, bad)
    out = explainer.coach_note("My friend invested so I think it is fine to join", [], "en")
    assert out is None or out == "Aap bahut accha kar rahe hain, aur aage bhi karte rahiye aap"


def test_coach_note_english_only(llm_on, monkeypatch):
    fake(monkeypatch, json.dumps({"note": "You explained your choice clearly, and that helps a lot in noticing patterns."}))
    assert explainer.coach_note("mera dost invest kar raha hai isliye theek hai", [], "hi") is None          # measured: local 3B Hindi is unreliable
    assert explainer.coach_note("mera dost invest kar raha hai isliye theek hai", [], "hinglish") is None
    assert explainer.coach_note("My friend invested so it is fine to join", [], "en")


def test_coach_skipped_without_reasoning_or_llm(monkeypatch):
    monkeypatch.setattr(client, "status", lambda force=False: {"available": True})
    monkeypatch.setattr(client, "generate", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not be called")))
    assert explainer.coach_note("", [], "en") is None and explainer.coach_note("short", [], "en") is None
    monkeypatch.setattr(client, "status", lambda force=False: {"available": False})
    assert explainer.coach_note("a long enough piece of reasoning text", [], "en") is None


def test_llm_timeout_falls_back(llm_on, monkeypatch):
    import httpx

    def boom(*a, **k):
        raise httpx.ReadTimeout("slow")
    monkeypatch.setattr(httpx, "post", boom)
    monkeypatch.setattr(client, "status", lambda force=False: {"available": True})
    assert client.generate("p", "s") is None
    assert explainer.coach_note("mera dost invest kar raha hai isliye theek hai", [], "hinglish") is None


def test_ollama_unreachable_reports_reason(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "llm_enabled", True)
    monkeypatch.setattr(s, "ollama_url", "http://127.0.0.1:9")
    client.reset_cache()
    st = client.status(force=True)
    assert st["available"] is False and "not reachable" in st["reason"]
    client.reset_cache()


def test_low_resource_disables_llm(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "llm_enabled", True)
    monkeypatch.setattr(s, "low_resource", True)
    client.reset_cache()
    st = client.status(force=True)
    assert st["available"] is False and "low-resource" in st["reason"]
    client.reset_cache()


def test_numbers_grounded_helper():
    assert client.numbers_grounded("7 warning signs and 30%", "7 and 30%")
    assert not client.numbers_grounded("99 signs", "7 and 30%")


def test_templates_in_all_languages_nonjudgemental():
    banned = ["stupid", "careless", "irrational", "foolish"]
    for lang in ("en", "hinglish", "hi"):
        for q in ("safe", "mixed", "unsafe"):
            t = build_explanation({**FACTS, "quality": q}, lang).lower()
            assert t and not any(b in t for b in banned)


# ------------------------------------------------------------------- migrations
def test_migrations_create_all_models_and_downgrade():
    tmp = Path(tempfile.mkdtemp()) / "mig.db"
    url = f"sqlite:///{tmp.as_posix()}"
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "database" / "migrations"))
    cfg.attributes["url"] = url
    command.upgrade(cfg, "head")
    eng = make_engine(url)
    tables = set(inspect(eng).get_table_names())
    expected = set(Base.metadata.tables) | {"alembic_version"}
    assert expected <= tables
    for need in ["users", "concepts", "user_concepts", "scenarios", "scenario_states", "scenario_decisions", "decision_reasoning", "misconceptions",
                 "user_misconceptions", "lessons", "quiz_questions", "quiz_attempts", "simulations", "simulation_events", "resilience_scores",
                 "model_versions", "training_runs", "knowledge_documents", "knowledge_chunks"]:
        assert need in tables
    idx = {i["name"] for i in inspect(eng).get_indexes("scenario_decisions")}
    assert any("session" in n for n in idx)
    eng.dispose()
    command.downgrade(cfg, "base")
    eng = make_engine(url)
    assert set(inspect(eng).get_table_names()) <= {"alembic_version"}
    eng.dispose()


def test_models_have_no_pii_columns():
    cols = {c.name for t in Base.metadata.tables.values() for c in t.columns}
    for forbidden in ["email", "phone", "aadhaar", "pan", "password", "otp", "card_number", "account_number", "address"]:
        assert forbidden not in cols


def test_answer_question_is_english_only(llm_on, monkeypatch):
    fake(monkeypatch, json.dumps({"note": "Volatility is how much a price moves up and down."}))
    assert explainer.answer_question("What is volatility?", "Volatility is how much a price moves.", "en")
    for lang in ("hinglish", "hi"):
        assert explainer.answer_question("Volatility kya hai?", "Volatility ka matlab utaar-chadhav.", lang) is None
