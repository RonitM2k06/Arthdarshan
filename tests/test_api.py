import random
import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from apps.api.main import app
from database import models as m
from database import session as dbs


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def new_user(client, **kw):
    r = client.post("/api/auth/start", json={"display_name": "Tester", **kw})
    assert r.status_code == 200
    j = r.json()
    return {"Authorization": f"Bearer {j['token']}"}, j["user"]


def start(client, h, sid="guaranteed_opportunity"):
    r = client.post("/api/scenarios/start", json={"scenario_id": sid}, headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def decide(client, h, sess, state, action, **kw):
    body = {"session_id": sess, "state_key": state, "action_id": action, **kw}
    return client.post("/api/decisions", json=body, headers=h)


# ---------------------------------------------------------------- basics
def test_health_and_components(client):
    j = client.get("/api/health").json()
    assert j["status"] == "ok" and j["scenarios"] >= 8 and j["offline_core"] is True
    assert set(j["components"]) >= {"llm", "embeddings", "stt", "tts", "ml"}


def test_auth_required_and_invalid_token(client):
    assert client.get("/api/users/me").status_code == 401
    assert client.get("/api/users/me", headers={"Authorization": "Bearer nope"}).status_code == 401
    assert client.post("/api/scenarios/start", json={"scenario_id": "x"}).status_code == 401


def test_profile_has_no_pii_fields(client):
    h, u = new_user(client)
    assert set(u) == {"public_id", "display_name", "language", "simple_mode", "is_demo", "streak_days", "created_at"}
    r = client.patch("/api/users/me", json={"language": "hinglish", "simple_mode": True}, headers=h)
    assert r.json()["language"] == "hinglish" and r.json()["simple_mode"] is True
    assert client.patch("/api/users/me", json={"language": "klingon"}, headers=h).status_code == 422
    assert client.patch("/api/users/me", json={"email": "a@b.c"}, headers=h).status_code == 422


def test_scenario_list_and_card(client):
    h, _ = new_user(client)
    j = client.get("/api/scenarios", headers=h).json()
    assert len(j["scenarios"]) >= 8 and j["scenarios"][0]["id"] == "guaranteed_opportunity"
    assert "NO REAL MONEY" in j["disclaimer"]
    assert client.get("/api/scenarios/nope", headers=h).status_code == 404


# ---------------------------------------------------------------- input validation
def test_decision_validation(client):
    h, _ = new_user(client)
    s = start(client, h)
    sid = s["session_id"]
    assert client.post("/api/decisions", json={}, headers=h).status_code == 422
    assert client.post("/api/decisions", content="not json", headers={**h, "Content-Type": "application/json"}).status_code == 422
    assert decide(client, h, sid, "s1_message", "walk", confidence=9).status_code == 422
    assert decide(client, h, sid, "s1_message", "walk", latency_ms=-5).status_code == 422
    assert decide(client, h, sid, "s1_message", "walk", reasoning="x" * 5000).status_code == 422
    assert decide(client, h, sid, "s1_message", "walk", extra_field=1).status_code == 422
    assert decide(client, h, "short", "s1_message", "walk").status_code == 422
    assert decide(client, h, "0" * 36, "s1_message", "walk").status_code == 404
    assert decide(client, h, sid, "s1_message", "does_not_exist").status_code == 400
    assert decide(client, h, sid, "s9_wrong", "walk").status_code == 409
    err = decide(client, h, sid, "s1_message", "does_not_exist").json()["error"]
    assert err["code"] == "invalid_action" and "Traceback" not in str(err)


def test_empty_reasoning_is_fine(client):
    h, _ = new_user(client)
    s = start(client, h)
    r = decide(client, h, s["session_id"], "s1_message", "walk", reasoning="")
    assert r.status_code == 200 and r.json()["terminal"] is True


def test_cannot_decide_after_finish_or_for_other_user(client):
    h1, _ = new_user(client)
    h2, _ = new_user(client)
    s = start(client, h1)
    assert decide(client, h2, s["session_id"], "s1_message", "walk").status_code == 404
    assert decide(client, h1, s["session_id"], "s1_message", "walk").status_code == 200
    assert decide(client, h1, s["session_id"], "s1_message", "walk").status_code == 409


def test_session_resume(client):
    h, _ = new_user(client)
    s = start(client, h)
    r = client.get(f"/api/scenarios/sessions/{s['session_id']}", headers=h).json()
    assert r["state"]["id"] == "s1_message" and r["status"] == "active"
    decide(client, h, s["session_id"], "s1_message", "investigate")
    r = client.get(f"/api/scenarios/sessions/{s['session_id']}", headers=h).json()
    assert r["state"]["id"] == "s6_investigation"


# ---------------------------------------------------------------- hero journey end to end
def test_hero_impulsive_then_careful_shows_improvement(client):
    h, _ = new_user(client)
    # RUN 1: impulsive
    s = start(client, h)
    sid = s["session_id"]
    assert s["state"]["pressure"] and any(p["type"] == "countdown" for p in s["state"]["pressure"])
    r1 = decide(client, h, sid, "s1_message", "invest", reasoning="My friend invested so it is probably legit and it is guaranteed", confidence=5,
                latency_ms=2000, evidence_noticed=["e_guar"]).json()
    a = r1["analysis"]
    assert a["quality"] == "unsafe"
    ids = {x["id"] for x in a["misconceptions"]}
    assert {"M001", "M011"} <= ids
    assert any(b["label"] == "friend_reliance" for b in a["behaviours"])
    assert a["evidence"]["missed"] and a["evidence"]["recognized"][0]["id"] == "e_guar"
    assert "fee" in r1["consequence"].lower() or "₹" in r1["consequence"]
    assert r1["next_state"]["id"] == "s2_fee" and not r1["terminal"]
    r2 = decide(client, h, sid, "s2_fee", "pay_fee", reasoning="I have already paid so I must pay once more to recover it", confidence=4, latency_ms=3000).json()
    assert "M010" in {x["id"] for x in r2["analysis"]["misconceptions"]}
    r3 = decide(client, h, sid, "s7_spiral", "pay_again", latency_ms=2500).json()
    assert r3["terminal"] and r3["summary"]["outcome"]["kind"] == "unsafe"
    fp1 = {d["id"]: d for d in r3["summary"]["fingerprint"]["dimensions"]}
    assert fp1["scam_awareness"]["score"] is not None and fp1["scam_awareness"]["score"] < 50
    assert fp1["fomo_resistance"]["score"] < 50
    assert fp1["concept_knowledge"]["score"] is None          # not measured yet: reported honestly, not invented
    assert r3["summary"]["misconceptions"]
    nxt = r3["summary"]["next"]
    assert nxt["scenario"]["rationale"] and nxt["scenario"]["reasons"] and nxt["selection_id"]
    # RUN 2: careful
    s2 = start(client, h)
    sid2 = s2["session_id"]
    ev = [e["id"] for e in s2["state"]["evidence"]]
    r = decide(client, h, sid2, "s1_message", "investigate", reasoning="Nobody can guarantee 30%, so I will verify it on the official website first", confidence=3,
               latency_ms=9000, evidence_noticed=[i for i in ev if i != "e_tone"]).json()
    assert r["analysis"]["quality"] == "safe" and r["analysis"]["evidence"]["recall"] == 1.0
    assert not any(x["id"] == "M001" for x in r["analysis"]["misconceptions"])   # sceptical sentence is not the misconception
    labels = {b["label"] for b in r["analysis"]["behaviours"]}
    assert "evidence_seeking" in labels
    r = decide(client, h, sid2, "s6_investigation", "report_leave", reasoning="No registration found so I will report it", confidence=4, latency_ms=8000,
               evidence_noticed=["i_dir", "i_guar", "i_acct"]).json()
    assert r["terminal"] and r["summary"]["outcome"]["kind"] == "safe"
    fp2 = {d["id"]: d for d in r["summary"]["fingerprint"]["dimensions"]}
    assert fp2["scam_awareness"]["score"] > fp1["scam_awareness"]["score"]
    assert fp2["scam_awareness"]["previous"] == pytest.approx(fp1["scam_awareness"]["score"])
    assert fp2["scam_awareness"]["change"] > 0
    assert fp2["evidence_verification"]["score"] > fp1["evidence_verification"]["score"]
    # report reflects the real data
    rep = client.get("/api/resilience/report", headers=h).json()
    assert rep["totals"] == {"decisions": 5, "scenarios_completed": 2}
    assert len(rep["improvement"]["points"]) == 2 and rep["improvement"]["first_to_latest"]["scam_awareness"] > 0
    assert rep["recognized"] and rep["missed"] and rep["behaviours"] and rep["scenario_performance"][0]["outcome"] == "unsafe"
    assert rep["decision_speed"]["median_s"] is not None
    dash = client.get("/api/progress", headers=h).json()
    assert dash["scenarios_completed"] == 2 and len(dash["recent_decisions"]) == 5 and dash["streak_days"] == 1


def test_misconception_resolution_over_time(client):
    h, _ = new_user(client)
    for _ in range(3):
        s = start(client, h)
        sid = s["session_id"]
        if _ == 0:
            decide(client, h, sid, "s1_message", "invest", reasoning="it is guaranteed so great", latency_ms=1500)
            decide(client, h, sid, "s2_fee", "stop_pay", latency_ms=4000)
        else:
            decide(client, h, sid, "s1_message", "walk", reasoning="no one can guarantee that", latency_ms=5000)
    rows = {r["id"]: r for r in client.get("/api/resilience/report", headers=h).json()["misconceptions"]}
    assert rows["M001"]["detections"] == 1 and rows["M001"]["status"] == "resolved" and rows["M001"]["clean_streak"] >= 2


def test_sensitive_data_is_redacted_before_storage(client):
    h, _ = new_user(client)
    s = start(client, h)
    r = decide(client, h, s["session_id"], "s1_message", "walk", reasoning="my pan is ABCDE1234F and otp is 482913 please check").json()
    assert "sensitive_data" in r["analysis"]["safety"]["flags"]
    with dbs.session_scope() as db:
        txt = db.scalars(select(m.DecisionReasoning.text).order_by(m.DecisionReasoning.id.desc())).first()
    assert "ABCDE1234F" not in txt and "482913" not in txt and "[REDACTED]" in txt


def test_advice_seeking_in_reasoning_is_flagged_not_answered(client):
    h, _ = new_user(client)
    s = start(client, h)
    r = decide(client, h, s["session_id"], "s1_message", "walk", reasoning="Which stock should I buy instead?").json()
    flags = r["analysis"]["safety"]
    assert "recommendation" in flags["flags"] and flags["message"]
    assert "buy" not in r["analysis"]["explanation"].lower() or "stock" not in r["analysis"]["explanation"].lower()


# ---------------------------------------------------------------- every scenario is playable end to end
SCEN = ["guaranteed_opportunity", "whatsapp_expert", "market_shock", "one_basket", "hidden_fee", "urgent_decision", "confusing_document", "family_file"]


@pytest.mark.parametrize("sid", SCEN)
def test_scenario_playable_safe_path(client, sid):
    h, _ = new_user(client)
    s = start(client, h, sid)
    state = s["state"]
    from apps.api.services.content import load_scenarios
    sc = load_scenarios()[sid]
    steps = 0
    while True:
        st = sc.states[state["id"]]
        act = next(a for a in st.actions if a.quality == "safe")
        r = decide(client, h, s["session_id"], state["id"], act.id, reasoning="I will check first", confidence=3, latency_ms=6000).json()
        steps += 1
        assert steps < 30
        if r["terminal"]:
            assert r["summary"]["outcome"]["kind"] in ("safe", "mixed")
            assert r["summary"]["micro_lesson"]["body"] and r["summary"]["reflection"]["key_points"]
            break
        state = r["next_state"]


@pytest.mark.parametrize("sid", SCEN)
def test_scenario_random_walks_always_terminate(client, sid):
    h, _ = new_user(client)
    rng = random.Random(7)
    from apps.api.services.content import load_scenarios
    sc = load_scenarios()[sid]
    for _ in range(4):
        s = start(client, h, sid)
        state_id = s["state"]["id"]
        for _step in range(40):
            act = rng.choice(sc.states[state_id].actions)
            r = decide(client, h, s["session_id"], state_id, act.id, latency_ms=rng.randint(300, 20000)).json()
            if r["terminal"]:
                break
            state_id = r["next_state"]["id"]
        else:
            pytest.fail("did not terminate")


def test_languages_localise_scenario_text(client):
    h, _ = new_user(client)
    en = client.post("/api/scenarios/start", json={"scenario_id": "guaranteed_opportunity"}, headers={**h, "X-Arth-Lang": "en"}).json()
    hi = client.post("/api/scenarios/start", json={"scenario_id": "guaranteed_opportunity"}, headers={**h, "X-Arth-Lang": "hi"}).json()
    hg = client.post("/api/scenarios/start", json={"scenario_id": "guaranteed_opportunity"}, headers={**h, "X-Arth-Lang": "hinglish"}).json()
    assert en["state"]["narrative"] != hi["state"]["narrative"] != hg["state"]["narrative"]
    assert "राहुल" in hi["state"]["narrative"] and "Rahul" in hg["state"]["narrative"]
    assert [a["id"] for a in en["state"]["actions"]] == [a["id"] for a in hi["state"]["actions"]]


def test_simple_mode_uses_short_labels(client):
    h, _ = new_user(client, simple_mode=True)
    s = start(client, h)
    labels = [a["label"] for a in s["state"]["actions"]]
    assert "Invest now" in labels and "Walk away" in labels and all(len(l) < 40 for l in labels)


def test_public_view_never_leaks_answers(client):
    h, _ = new_user(client)
    s = start(client, h)
    blob = str(s["state"])
    assert "quality" not in blob and "red_flag" not in blob and "'why'" not in blob and "kind" not in blob


# ---------------------------------------------------------------- concurrency
def test_concurrent_sessions_are_isolated(client):
    h, _ = new_user(client)
    sessions_ = [start(client, h)["session_id"] for _ in range(6)]
    results, errors = {}, []

    def play(i, sid):
        try:
            action = "walk" if i % 2 == 0 else "investigate"
            r = client.post("/api/decisions", json={"session_id": sid, "state_key": "s1_message", "action_id": action, "latency_ms": 1000 + i}, headers=h)
            results[i] = r.json()
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    ts = [threading.Thread(target=play, args=(i, sid)) for i, sid in enumerate(sessions_)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errors
    for i, r in results.items():
        assert ("summary" in r) == (i % 2 == 0)
        assert r["terminal"] == (i % 2 == 0)


# ---------------------------------------------------------------- privacy / reset
def test_export_reset_and_delete(client):
    h, _ = new_user(client)
    s = start(client, h)
    decide(client, h, s["session_id"], "s1_message", "walk", reasoning="no one can guarantee that")
    exp = client.get("/api/users/me/export", headers=h).json()
    assert exp["decisions"] and "token_hash" not in str(exp)
    r = client.delete("/api/users/me/data", headers=h).json()
    assert r["profile_kept"] and r["deleted"]["sessions"] >= 1
    assert client.get("/api/progress", headers=h).json()["scenarios_completed"] == 0
    assert client.get("/api/users/me", headers=h).status_code == 200
    assert client.delete("/api/users/me", headers=h).status_code == 200
    assert client.get("/api/users/me", headers=h).status_code == 401
    with dbs.session_scope() as db:
        assert db.scalar(select(m.ScenarioDecision).where(m.ScenarioDecision.session_id == s["session_id"])) is None


# ---------------------------------------------------------------- simulations / learning / rag / safety / voice
def test_simulation_endpoints(client):
    h, _ = new_user(client)
    cat = client.get("/api/simulations", headers=h).json()
    assert len(cat["simulations"]) == 9 and "NO REAL MONEY" in cat["label"]
    r = client.post("/api/simulations/fee_erosion/run", json={"params": {"amount": 100000, "years": 20, "growth": 8, "fee": 2.5}}, headers=h)
    assert r.status_code == 200 and r.json()["summary"]["final_net"] < r.json()["summary"]["final_gross"]
    assert client.post("/api/simulations/fee_erosion/run", json={"params": {"years": 999}}, headers=h).status_code == 422
    assert client.post("/api/simulations/nope/run", json={"params": {}}, headers=h).status_code == 422
    assert client.post("/api/simulations/fee_erosion/run", json={"params": {"amount": "x"}}, headers=h).status_code == 422


def test_quiz_flow_updates_mastery_and_misconceptions(client):
    h, _ = new_user(client)
    qs = client.get("/api/learning/quiz?concept=risk", headers=h).json()["questions"]
    assert qs and "correct_index" not in str(qs)
    q = qs[0]
    wrong = client.post("/api/learning/quiz/answer", json={"question_id": q["id"], "selected_index": 0}, headers=h).json()
    assert wrong["correct"] is False and wrong["misconception"]["id"] == "M005"
    right = client.post("/api/learning/quiz/answer", json={"question_id": q["id"], "selected_index": wrong["correct_index"]}, headers=h).json()
    assert right["correct"] is True and right["mastery"] is not None
    assert client.post("/api/learning/quiz/answer", json={"question_id": q["id"], "selected_index": 7}, headers=h).status_code == 400
    assert client.post("/api/learning/quiz/answer", json={"question_id": "none", "selected_index": 0}, headers=h).status_code == 404


def test_concept_graph(client):
    h, _ = new_user(client)
    g = client.get("/api/concepts", headers=h).json()
    ids = {n["id"] for n in g["nodes"]}
    for need in ["saving", "inflation", "compounding", "risk", "volatility", "diversification", "concentration_risk", "liquidity", "stock", "mutual_fund",
                 "sip", "nav", "bond", "etf", "kyc", "nomination", "fees", "fraud_red_flags", "verification", "financial_disclosures", "social_proof", "fomo"]:
        assert need in ids
    assert g["edges"]
    c = client.get("/api/concepts/volatility", headers={**h, "X-Arth-Lang": "hinglish"}).json()
    assert "Volatility" in c["simple"] and c["examples"] and c["related"] and c["detailed"]


def test_rag_grounded_with_citations_and_refusal(client):
    h, _ = new_user(client)
    r = client.post("/api/rag/ask", json={"question": "Why is a guaranteed return a red flag?"}, headers=h).json()
    assert r["grounded"] and r["citations"] and r["blocked"] is False
    assert all(c["title"] and c["source"] and "verified_official" in c for c in r["citations"])
    out = client.post("/api/rag/ask", json={"question": "What is the penalty under section 12B for late filing in Zimbabwe?"}, headers=h).json()
    assert out["grounded"] is False and "enough verified information" in out["answer"] and out["citations"] == []
    hg = client.post("/api/rag/ask", json={"question": "Volatility kya hoti hai?"}, headers=h).json()
    assert hg["language"] == "hinglish" and "utaar" in hg["answer"].lower()


def test_rag_blocks_advice_questions(client):
    h, _ = new_user(client)
    for q in ["What stock should I buy tomorrow?", "Which mutual fund is best?", "Predict NIFTY tomorrow.", "Tell me where I should invest ₹50,000."]:
        r = client.post("/api/rag/ask", json={"question": q}, headers=h).json()
        assert r["blocked"] is True and r["citations"] == [] and r["safety"]["categories"]
        assert "doesn't tell" in r["answer"] or "can't" in r["answer"] or "Nobody can" in r["answer"]


def test_safety_check_endpoint(client):
    h, _ = new_user(client)
    r = client.post("/api/safety/check", json={"text": "You should buy this stock.", "direction": "output"}, headers=h).json()
    assert r["allowed"] is False and r["action"] == "rewrite"
    r = client.post("/api/safety/check", json={"text": "Which stock should I buy?"}, headers=h).json()
    assert r["allowed"] is False
    assert client.post("/api/safety/check", json={"text": "x" * 9000}, headers=h).status_code == 422


def test_evidence_lab(client):
    h, _ = new_user(client)
    r = client.post("/api/learning/evidence-lab/analyze", json={"question": "SEBI registered opportunity. Guaranteed 30% returns. Only 10 slots remaining. Invest today."}, headers=h).json()
    assert r["signals_found"] >= 4 and r["level"] == "many" and len(r["workflow"]) == 6
    assert any(q["signals"] for q in r["questions"]) and r["missing_information"]
    calm = client.post("/api/learning/evidence-lab/analyze", json={"question": "Aakash Debt Opportunities Fund Pvt Ltd. Returns are not guaranteed and may fall. Exit load 1% within 12 months."}, headers=h).json()
    assert calm["level"] in ("none", "few")
    red = client.post("/api/learning/evidence-lab/analyze", json={"question": "my otp is 482913 guaranteed returns"}, headers=h).json()
    assert red["safety"]["redactions"]


def test_voice_status_and_text_ask_with_fallbacks(client):
    h, _ = new_user(client)
    st = client.get("/api/voice/status", headers=h).json()
    assert st["browser_fallback"] is True and "stt" in st and "tts" in st
    r = client.post("/api/voice/ask", data={"question": "Volatility kya hoti hai?", "language_hint": "hinglish", "speak_answer": "false"}, headers=h).json()
    assert r["transcript"] == "Volatility kya hoti hai?" and r["grounded"] and r["language"] == "hinglish"
    assert client.post("/api/voice/ask", data={"question": ""}, headers=h).status_code == 400
    bad = client.post("/api/voice/transcribe", files={"audio": ("a.webm", b"tiny")}, headers=h)
    assert bad.status_code in (400, 503)          # microphone/STT problems degrade to a clear message, never a crash


def test_models_endpoint(client):
    h, _ = new_user(client)
    j = client.get("/api/models", headers=h).json()
    assert "components" in j and "model_versions" in j


def test_database_failure_is_a_safe_503(client):
    def broken():
        raise OperationalError("SELECT 1", {}, Exception("database is locked"))
        yield  # pragma: no cover
    h, _ = new_user(client)
    app.dependency_overrides[dbs.get_db] = broken
    try:
        r = client.get("/api/scenarios", headers=h)
    finally:
        app.dependency_overrides.clear()
    assert r.status_code in (503, 500)
    assert "locked" not in r.text and "Traceback" not in r.text


def test_unknown_route_and_method(client):
    assert client.get("/api/nope").status_code == 404
    assert client.put("/api/health").status_code == 405


def test_scripted_demo_persona_runs_through_the_real_engine(client):
    r = client.post("/api/auth/demo-persona", json={"language": "en"})
    assert r.status_code == 200 and "scripted" in r.json()["user"]["display_name"]
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    rep = client.get("/api/resilience/report", headers=h).json()
    assert rep["totals"]["scenarios_completed"] == 5 and rep["totals"]["decisions"] >= 12
    assert len(rep["improvement"]["points"]) == 5 and rep["improvement"]["first_to_latest"]
    assert any(m["status"] in ("improving", "resolved") for m in rep["misconceptions"])
    dims = {d["id"]: d for d in rep["fingerprint"]["dimensions"]}
    assert dims["scam_awareness"]["score"] is not None and dims["scam_awareness"]["change"] is not None
