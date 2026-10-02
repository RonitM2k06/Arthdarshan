"""Scenario session flow. The deterministic engine owns truth; this layer records, analyses and explains.

decision pipeline:
  input safety -> engine.step (truth) -> misconception + behaviour analysis -> persist -> observations
  -> concept mastery (BKT) -> explanation (LLM or template, safety-checked) -> response
on a terminal state: finalize (summary, fingerprint snapshot, misconception exposures, next recommendation)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.adaptive_learning.dimensions import DIMS, lang_of
from ai.adaptive_learning.policy import rank_scenarios, recommend_other
from ai.llm.explainer import coach_note, explain_decision
from ai.llm.templates import PRESSURE_NAMES
from ai.misconception import behaviour as bh
from ai.misconception import detector, ml_models
from ai.scenario_engine import engine as eng
from ai.scenario_engine.schema import Scenario
from ai.safety.gateway import check_input, check_output
from apps.api.errors import AppError
from apps.api.services import learner, scoring
from apps.api.services.content import load_scenarios
from apps.api.schemas.core import DecisionIn
from database import models as m

log = logging.getLogger("arth.sessions")
MAX_LATENCY_MS = 3_600_000


def now() -> datetime:
    return datetime.now(timezone.utc)


def get_scenario(scenario_id: str) -> Scenario:
    sc = load_scenarios().get(scenario_id)
    if sc is None:
        raise AppError(404, "scenario_not_found", f"Unknown scenario '{scenario_id}'.")
    return sc


def scenario_card(sc: Scenario, lang: str = "en") -> dict:
    loc = eng.localize(sc, lang if lang != "hi" else "hi")
    return {"id": sc.id, "title": loc.title, "tagline": loc.tagline, "difficulty": sc.difficulty, "character": loc.character.model_dump(),
            "concept_tags": sc.concept_tags, "pressure_tags": sc.pressure_tags, "dimensions": sc.scoring.dimensions,
            "disclaimer": sc.disclaimer, "states": len(sc.states),
            "languages": ["en"] + list(sc.i18n)}


def _view(sc: Scenario, state_key: str, lang: str, simple: bool) -> dict:
    loc = eng.localize(sc, lang)
    view = eng.public_state_view(loc, state_key, simple=simple)
    view["disclaimer"] = sc.disclaimer
    return view


def _own(db: Session, user: m.User, session_id: str) -> m.ScenarioSession:
    sess = db.get(m.ScenarioSession, session_id)
    if sess is None or sess.user_id != user.id:
        raise AppError(404, "session_not_found", "Session not found.")
    return sess


def start_session(db: Session, user: m.User, scenario_id: str, lang: str, selection_id: int | None = None) -> dict:
    sc = get_scenario(scenario_id)
    errs = eng.validate_scenario(sc)
    if errs:  # defence in depth: never run an invalid scenario
        log.error("scenario %s invalid: %s", scenario_id, errs)
        raise AppError(500, "scenario_invalid", "This scenario is unavailable.")
    if selection_id is not None:
        sel = db.get(m.AdaptiveSelection, selection_id)
        if sel is None or sel.user_id != user.id:
            selection_id = None
    row_sc = db.get(m.Scenario, scenario_id)
    sess = m.ScenarioSession(id=str(uuid.uuid4()), user_id=user.id, scenario_id=scenario_id, scenario_version=row_sc.version if row_sc else 1,
                             current_state_key=sc.initial_state, status="active", path=[{"state": sc.initial_state, "shown_at": now().isoformat()}],
                             selection_id=selection_id)
    db.add(sess)
    learner.touch_streak(user)
    db.commit()
    return {"session_id": sess.id, "scenario": scenario_card(sc, lang), "state": _view(sc, sc.initial_state, lang, user.simple_mode),
            "step": 1}


def resume_session(db: Session, user: m.User, session_id: str, lang: str) -> dict:
    sess = _own(db, user, session_id)
    sc = get_scenario(sess.scenario_id)
    out = {"session_id": sess.id, "status": sess.status, "scenario": scenario_card(sc, lang),
           "state": _view(sc, sess.current_state_key, lang, user.simple_mode), "step": len(sess.decisions) + 1}
    if sess.status == "completed":
        out["summary"] = sess.summary
    return out


def abandon_session(db: Session, user: m.User, session_id: str) -> None:
    sess = _own(db, user, session_id)
    if sess.status == "active":
        sess.status = "abandoned"
        db.commit()


def _server_latency_ms(sess: m.ScenarioSession) -> int | None:
    try:
        shown = datetime.fromisoformat(sess.path[-1]["shown_at"])
        return int((now() - shown).total_seconds() * 1000)
    except Exception:  # noqa: BLE001
        return None


def decide(db: Session, user: m.User, body: DecisionIn, lang: str) -> dict:
    sess = _own(db, user, body.session_id)
    if sess.status != "active":
        raise AppError(409, "session_not_active", "This scenario session has already finished.")
    if sess.current_state_key != body.state_key:
        raise AppError(409, "state_mismatch", "The scenario has moved on. Reload to continue.")
    sc = get_scenario(sess.scenario_id)
    loc = eng.localize(sc, lang)
    state, loc_state = sc.states[body.state_key], loc.states[body.state_key]

    # 1) INPUT SAFETY on free text
    safety = check_input(body.reasoning or "", lang)
    reasoning = safety.text
    flags = list(safety.categories)

    # 2) DETERMINISTIC TRUTH
    try:
        step = eng.step(sc, body.state_key, body.action_id, body.evidence_noticed)
    except eng.InvalidAction as exc:
        raise AppError(400, "invalid_action", str(exc)) from exc
    latency = body.latency_ms
    if latency is None:
        latency = _server_latency_ms(sess)
    latency = None if latency is None else max(0, min(latency, MAX_LATENCY_MS))
    countdown_expired = bool(body.countdown_expired or (step.countdown_seconds and latency is not None and latency > step.countdown_seconds * 1000))

    # 3) ANALYSIS (rules + trained models + choice signals); LLM is not consulted here
    ml_p = ml_models.predict_misconceptions(reasoning)
    dets = detector.detect(reasoning, step.misconception_signals, ml_p, ml_models.misconception_threshold())
    beh_ml = [bh.BehaviourHit(k, v, "ml") for k, v in ml_models.predict_behaviours(reasoning).items() if v >= ml_models.behaviour_threshold()]
    behs = bh.merge(bh.classify_rules(reasoning), beh_ml,
                    bh.classify_context(step.quality, step.pressure_types, latency, step.evidence.recall, step.requests_evidence, step.verification))
    emotions = bh.emotional_indicators(reasoning)
    uncertainty = bh.has_uncertainty_recognition(reasoning)

    # 4) PERSIST
    decision = m.ScenarioDecision(session_id=sess.id, user_id=user.id, state_key=body.state_key, action_id=step.action_id,
                                  action_quality=step.quality, next_state_key=step.next_state_key, latency_ms=latency,
                                  confidence=body.confidence, pressure_types=step.pressure_types, countdown_expired=countdown_expired,
                                  evidence_noticed=step.evidence.noticed_red_flags + [e for e in step.evidence.false_alarms],
                                  evidence_missed=step.evidence.missed_red_flags,
                                  evidence_requested=[step.action_id] if (step.requests_evidence or step.verification) else [])
    db.add(decision)
    db.flush()
    loc_ev = {e.id: e for e in loc_state.evidence}
    facts = {
        "scenario_title": loc.title, "state_title": loc_state.title,
        "action_label": next(a.label for a in loc_state.actions if a.id == step.action_id), "quality": step.quality,
        "pressure_types": step.pressure_types, "red_flag_total": len(step.evidence.red_flags),
        "noticed": [{"id": i, "label": loc_ev[i].label, "why": loc_ev[i].why} for i in step.evidence.noticed_red_flags],
        "missed": [{"id": i, "label": loc_ev[i].label, "why": loc_ev[i].why} for i in step.evidence.missed_red_flags],
        "behaviours": [bh.explain(h.label, lang) for h in behs[:3]],
        "misconceptions": [detector.correction(d.id, lang) for d in dets[:2]], "confidence": body.confidence,
    }
    explanation, source = explain_decision(facts, lang)          # deterministic, factual
    guard = check_output(explanation, lang)
    if not guard.allowed:
        explanation = guard.text
    coach = coach_note(reasoning, [b["name"] for b in facts["behaviours"]], lang)   # optional local-LLM reflection on the learner's own words
    if coach:
        source = "llm"
    db.add(m.DecisionReasoning(decision_id=decision.id, text=reasoning, safety_flags=flags, behaviours=[h.label for h in behs],
                               misconceptions=[d.to_dict() for d in dets], emotional_indicators=emotions, uncertainty_recognized=uncertainty,
                               explanation=explanation, explanation_source=source))
    for d in dets:
        learner.record_detection(db, user.id, d.id)
    obs = scoring.observations_for_decision(
        sc, state, step, confidence=body.confidence, latency_ms=latency, behaviours=[h.label for h in behs], emotions=emotions,
        uncertainty=uncertainty, text_detections=sum(1 for d in dets if "rule" in d.source or "ml" in d.source))
    scoring.store_observations(db, user.id, "decision", str(decision.id), obs)
    action = next(a for a in state.actions if a.id == step.action_id)
    learner.update_concepts(db, user.id, action.concept_tags or sc.concept_tags[:3], step.quality)
    learner.touch_streak(user)

    # 5) ADVANCE STATE
    sess.current_state_key = step.next_state_key
    sess.path = list(sess.path) + [{"state": step.next_state_key, "shown_at": now().isoformat()}]
    decision.analysis = {"behaviours": [h.label for h in behs], "misconceptions": [d.id for d in dets], "observations": [o.dimension for o in obs]}
    db.flush()

    loc_action = next(a for a in loc_state.actions if a.id == step.action_id)
    analysis = {
        "quality": step.quality, "explanation": explanation, "explanation_source": source, "coach_note": coach,
        "evidence": {"recall": step.evidence.recall,
                     "recognized": [{"id": i, "label": loc_ev[i].label, "why": loc_ev[i].why} for i in step.evidence.noticed_red_flags],
                     "missed": [{"id": i, "label": loc_ev[i].label, "why": loc_ev[i].why} for i in step.evidence.missed_red_flags],
                     "false_alarms": [{"id": i, "label": loc_ev[i].label, "why": loc_ev[i].why} for i in step.evidence.false_alarms]},
        "behaviours": [bh.explain(h.label, lang) | {"confidence": round(h.confidence, 2), "source": h.source} for h in behs[:4]],
        "misconceptions": [detector.correction(d.id, lang) | {"source": d.source, "confidence": round(d.confidence, 2)} for d in dets],
        "pressure": [{"type": p.type, "text": p.text} for p in loc_state.pressure],
        "pressure_response": ("held_steady" if step.quality == "safe" else "partly" if step.quality == "mixed" else "acted") if state.pressure else None,
        "latency_ms": latency, "countdown_expired": countdown_expired, "emotions": emotions, "uncertainty_recognized": uncertainty,
        "safety": {"flags": flags, "message": safety.message if flags else None, "redactions": safety.redactions},
    }
    result: dict = {"decision_id": decision.id, "consequence": loc_action.consequence, "analysis": analysis, "terminal": step.terminal}
    if step.terminal:
        result["summary"] = finalize(db, user, sess, sc, lang)
    else:
        result["next_state"] = _view(sc, step.next_state_key, lang, user.simple_mode)
        result["step"] = len(sess.decisions) + 1
    db.commit()
    return result


def _collect_summary_evidence(sess: m.ScenarioSession, loc: Scenario) -> tuple[list[dict], list[dict]]:
    recognized, missed = [], []
    for d in sess.decisions:
        st = loc.states[d.state_key]
        ev = {e.id: e for e in st.evidence}
        for i in d.evidence_noticed:
            if i in ev and ev[i].kind == "red_flag":
                recognized.append({"id": i, "label": ev[i].label, "why": ev[i].why, "state": st.title})
        for i in d.evidence_missed:
            if i in ev:
                missed.append({"id": i, "label": ev[i].label, "why": ev[i].why, "state": st.title})
    return recognized, missed


def finalize(db: Session, user: m.User, sess: m.ScenarioSession, sc: Scenario, lang: str) -> dict:
    loc = eng.localize(sc, lang)
    terminal = loc.states[sess.current_state_key]
    outcome = terminal.outcome.model_dump() if terminal.outcome else {"kind": "mixed", "headline": "", "summary": ""}
    decisions = list(sess.decisions)
    recognized, missed = _collect_summary_evidence(sess, loc)
    total_red = len(recognized) + len(missed)
    detected: dict[str, dict] = {}
    beh_count: dict[str, int] = {}
    for d in decisions:
        for mi in (d.reasoning.misconceptions if d.reasoning else []):
            detected.setdefault(mi["id"], mi)
        for b in (d.reasoning.behaviours if d.reasoning else []):
            beh_count[b] = beh_count.get(b, 0) + 1
    lat = [d.latency_ms / 1000 for d in decisions if d.latency_ms is not None]
    under = [d for d in decisions if d.pressure_types]
    pressure = {"decisions_under_pressure": len(under), "held_steady": sum(1 for d in under if d.action_quality == "safe"),
                "acted_under_pressure": sum(1 for d in under if d.action_quality == "unsafe"),
                "types": sorted({t for d in under for t in d.pressure_types}),
                "countdown_expired": sum(1 for d in decisions if d.countdown_expired)}
    resolved = learner.close_exposures(db, user.id, sc.tests_misconceptions, set(detected))
    sess.status, sess.completed_at = "completed", now()
    db.flush()
    scoring.snapshot(db, user.id, sess.id)
    # concept mastery bonus for finishing safely
    learner.update_concepts(db, user.id, sc.concept_tags[:2], outcome["kind"])
    if sess.selection_id:
        sel = db.get(m.AdaptiveSelection, sess.selection_id)
        if sel:
            sel.outcome = outcome["kind"]
    db.flush()
    fp = scoring.fingerprint_view(db, user.id, lang)
    nxt = recommend_next(db, user, lang)
    ml = loc.reflection.micro_lesson
    summary = {
        "scenario_id": sc.id, "title": loc.title, "outcome": outcome,
        "decisions": [{"state": loc.states[d.state_key].title, "action": next((a.label for a in loc.states[d.state_key].actions if a.id == d.action_id), d.action_id),
                       "quality": d.action_quality, "latency_s": None if d.latency_ms is None else round(d.latency_ms / 1000, 1),
                       "confidence": d.confidence} for d in decisions],
        "evidence": {"recognized": recognized, "missed": missed, "recall": (len(recognized) / total_red) if total_red else None,
                     "requested_verification": sum(1 for d in decisions if d.evidence_requested)},
        "pressure": pressure,
        "decision_speed": {"avg_s": round(sum(lat) / len(lat), 1) if lat else None, "fastest_s": round(min(lat), 1) if lat else None,
                           "slowest_s": round(max(lat), 1) if lat else None},
        "behaviours": [bh.explain(b, lang) | {"count": c} for b, c in sorted(beh_count.items(), key=lambda kv: -kv[1]) if b in bh.BEHAVIOURS],
        "misconceptions": [detector.correction(i, lang) | {"source": d["source"]} for i, d in detected.items()],
        "misconceptions_resolved": [detector.correction(i, lang) for i in resolved],
        "micro_lesson": {"concept_id": ml.concept_id, "title": ml.title, "body": ml.body},
        "reflection": {"key_points": loc.reflection.key_points, "questions": loc.reflection.questions},
        "fingerprint": fp, "next": nxt, "disclaimer": sc.disclaimer,
    }
    sess.summary = summary
    return summary


def recommend_next(db: Session, user: m.User, lang: str = "en", persist: bool = True) -> dict:
    state = learner.build_user_state(db, user.id)
    scenarios = load_scenarios()
    titles = {sid: eng.localize(sc, lang).title for sid, sc in scenarios.items()}
    recent = state.completed[-5:]
    recent_rate = (sum(1 for _, o in recent if o == "safe") / len(recent)) if recent else 0.0
    avg_dim = (sum(s for s, _ in state.dimension_scores.values()) / len(state.dimension_scores) / 100) if state.dimension_scores else 0.5

    def success_fn(ready: float, difficulty: int, sc: Scenario) -> float:
        p = ml_models.success_probability([ready, difficulty, recent_rate, avg_dim, min(len(state.completed), 10) / 10])
        if p is not None:
            return max(0.05, min(0.95, p))
        from ai.adaptive_learning.policy import heuristic_success
        return heuristic_success(ready, difficulty)

    ranked = rank_scenarios(state, scenarios, titles, success_fn)
    top = ranked[0] if ranked else None
    others = recommend_other(state)
    out: dict = {"scenario": top.to_dict() if top else None, "alternatives": [r.to_dict() for r in ranked[1:3]],
                 "other_training": [o.to_dict() for o in others], "model": "ml_success_model" if ml_models.available("success_model") else "heuristic_readiness"}
    if top and persist:
        sel = m.AdaptiveSelection(user_id=user.id, weakness=top.weakness, selected_training=top.id, training_kind="scenario", difficulty=top.difficulty,
                                  rationale=top.rationale, mastery_estimate=top.mastery_estimate, predicted_success=top.predicted_success)
        db.add(sel)
        db.flush()
        out["selection_id"] = sel.id
    return out
