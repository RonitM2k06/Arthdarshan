"""Resilience report and dashboard. Every statement is computed from the learner's recorded interactions."""
from __future__ import annotations

import statistics
from collections import Counter, defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.adaptive_learning.dimensions import DIMS, lang_of
from ai.misconception import behaviour as bh
from ai.misconception import detector
from ai.scenario_engine import engine as eng
from apps.api.services import learner, scoring, sessions
from apps.api.services.content import load_concepts, load_scenarios
from database import models as m

PRESS_TIME = {"urgency", "countdown", "scarcity", "fomo"}


def _decisions(db: Session, user_id: int) -> list[m.ScenarioDecision]:
    return list(db.scalars(select(m.ScenarioDecision).where(m.ScenarioDecision.user_id == user_id).order_by(m.ScenarioDecision.id)))


def _completed(db: Session, user_id: int) -> list[m.ScenarioSession]:
    return list(db.scalars(select(m.ScenarioSession).where(m.ScenarioSession.user_id == user_id, m.ScenarioSession.status == "completed")
                           .order_by(m.ScenarioSession.completed_at)))


def improvement(db: Session, user_id: int, lang: str) -> dict:
    rows = list(db.scalars(select(m.ResilienceScore).where(m.ResilienceScore.user_id == user_id).order_by(m.ResilienceScore.id)))
    by_session: dict[str, dict[str, float]] = {}
    order: list[str] = []
    for r in rows:
        sid = r.session_id or "n/a"
        if sid not in by_session:
            by_session[sid] = {}
            order.append(sid)
        by_session[sid][r.dimension] = r.score
    # carry forward the latest known score so each point is a full fingerprint
    cur: dict[str, float] = {}
    points = []
    for i, sid in enumerate(order):
        cur.update(by_session[sid])
        sess = db.get(m.ScenarioSession, sid) if sid != "n/a" else None
        title = None
        if sess:
            sc = load_scenarios().get(sess.scenario_id)
            title = eng.localize(sc, lang).title if sc else sess.scenario_id
        points.append({"index": i + 1, "scenario": title, "overall": round(sum(cur.values()) / len(cur), 1), "dimensions": dict(cur)})
    delta = None
    if len(points) >= 2:
        first, last = points[0], points[-1]
        common = set(first["dimensions"]) & set(last["dimensions"])
        delta = {d: round(last["dimensions"][d] - first["dimensions"][d], 1) for d in common}
    return {"points": points, "first_to_latest": delta}


def build_report(db: Session, user: m.User, lang: str) -> dict:
    lang = lang_of(lang)
    decisions = _decisions(db, user.id)
    sess_list = _completed(db, user.id)
    scenarios = load_scenarios()
    session_cache: dict[str, m.ScenarioSession] = {s.id: s for s in db.scalars(select(m.ScenarioSession).where(m.ScenarioSession.user_id == user.id))}
    loc_cache = {sid: eng.localize(sc, lang) for sid, sc in scenarios.items()}

    recognized, missed = Counter(), Counter()
    labels: dict[tuple[str, str], tuple[str, str | None]] = {}
    for d in decisions:
        s = session_cache.get(d.session_id)
        if not s:
            continue
        loc = loc_cache[s.scenario_id]
        st = loc.states.get(d.state_key)
        if not st:
            continue
        ev = {e.id: e for e in st.evidence}
        for i in d.evidence_noticed:
            if i in ev and ev[i].kind == "red_flag":
                recognized[(s.scenario_id, i)] += 1
                labels[(s.scenario_id, i)] = (ev[i].label, ev[i].why)
        for i in d.evidence_missed:
            if i in ev:
                missed[(s.scenario_id, i)] += 1
                labels[(s.scenario_id, i)] = (ev[i].label, ev[i].why)

    def pack(counter: Counter, n: int = 6) -> list[dict]:
        return [{"label": labels[k][0], "why": labels[k][1], "times": c, "scenario": loc_cache[k[0]].title} for k, c in counter.most_common(n)]

    beh_counter: Counter = Counter()
    for r in db.scalars(select(m.DecisionReasoning).join(m.ScenarioDecision).where(m.ScenarioDecision.user_id == user.id)):
        for b in r.behaviours:
            beh_counter[b] += 1
    behaviours = [bh.explain(b, lang) | {"count": c} for b, c in beh_counter.most_common() if b in bh.BEHAVIOURS]

    misc_rows = list(db.scalars(select(m.UserMisconception).where(m.UserMisconception.user_id == user.id)))
    misconceptions = [detector.correction(r.misconception_id, lang) | {"detections": r.detections, "exposures": r.exposures,
                                                                       "status": r.status, "clean_streak": r.clean_streak} for r in misc_rows]
    cnames = {c["id"]: c["name"][lang] for c in load_concepts()}
    mastery_rows = list(db.scalars(select(m.UserConcept).where(m.UserConcept.user_id == user.id).order_by(m.UserConcept.mastery.desc())))
    concepts = [{"id": r.concept_id, "name": cnames.get(r.concept_id, r.concept_id), "mastery": round(r.mastery, 2), "attempts": r.attempts,
                 "correct": r.correct, "mastered": r.mastery >= 0.8} for r in mastery_rows]

    performance = []
    for s in sess_list:
        out = (s.summary or {}).get("outcome", {})
        performance.append({"session_id": s.id, "scenario_id": s.scenario_id, "title": loc_cache[s.scenario_id].title, "outcome": out.get("kind"),
                            "headline": out.get("headline"), "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                            "decisions": len(s.decisions), "simulated_loss": out.get("simulated_loss")})

    lat_all = [d.latency_ms for d in decisions if d.latency_ms is not None]
    pressured = [d for d in decisions if d.latency_ms is not None and (set(d.pressure_types) & PRESS_TIME)]
    unpressured = [d for d in decisions if d.latency_ms is not None and not (set(d.pressure_types) & PRESS_TIME)]
    unsafe_lat = [d.latency_ms for d in decisions if d.latency_ms is not None and d.action_quality == "unsafe"]
    safe_lat = [d.latency_ms for d in decisions if d.latency_ms is not None and d.action_quality == "safe"]
    med = lambda xs: round(statistics.median(xs) / 1000, 1) if xs else None  # noqa: E731
    speed = {"median_s": med(lat_all), "under_time_pressure_median_s": med([d.latency_ms for d in pressured]),
             "without_time_pressure_median_s": med([d.latency_ms for d in unpressured]),
             "unsafe_choices_median_s": med(unsafe_lat), "safe_choices_median_s": med(safe_lat), "n": len(lat_all)}

    def ver_rate(ds: list[m.ScenarioDecision]) -> float | None:
        # decisions where an independent-verification action existed in the state
        eligible = []
        for d in ds:
            s = session_cache.get(d.session_id)
            if not s:
                continue
            st = scenarios[s.scenario_id].states.get(d.state_key)
            if st and any(a.verification is True for a in st.actions):
                eligible.append(d)
        if not eligible:
            return None
        ok = 0
        for d in eligible:
            st = scenarios[session_cache[d.session_id].scenario_id].states[d.state_key]
            if next((a for a in st.actions if a.id == d.action_id), None) and next(a for a in st.actions if a.id == d.action_id).verification is True:
                ok += 1
        return round(ok / len(eligible), 2)

    ev_usage = {"verification_rate_overall": ver_rate(decisions), "verification_rate_under_time_pressure": ver_rate(pressured),
                "verification_rate_without_time_pressure": ver_rate(unpressured),
                "avg_warning_sign_recall": (lambda r: round(sum(r) / len(r), 2) if r else None)(
                    [(s.summary or {}).get("evidence", {}).get("recall") for s in sess_list if (s.summary or {}).get("evidence", {}).get("recall") is not None])}

    fp = scoring.fingerprint_view(db, user.id, lang)
    impr = improvement(db, user.id, lang)
    nxt = sessions.recommend_next(db, user, lang, persist=False)

    insights: list[str] = []
    top_rec = recognized.most_common(1)
    if top_rec:
        k, c = top_rec[0]
        insights.append({"en": f"You identified “{labels[k][0]}” in {c} decision(s).", "hinglish": f"Aapne “{labels[k][0]}” ko {c} faisle(on) mein pehchana.",
                         "hi": f"आपने “{labels[k][0]}” को {c} फ़ैसले(लों) में पहचाना।"}[lang])
    if speed["under_time_pressure_median_s"] is not None and speed["without_time_pressure_median_s"] is not None \
            and speed["under_time_pressure_median_s"] < speed["without_time_pressure_median_s"] * 0.7:
        insights.append({"en": f"You decided faster under time pressure ({speed['under_time_pressure_median_s']}s) than without it ({speed['without_time_pressure_median_s']}s).",
                         "hinglish": f"Time pressure mein aapne tezi se faisla kiya ({speed['under_time_pressure_median_s']}s) jabki bina pressure ke ({speed['without_time_pressure_median_s']}s).",
                         "hi": f"समय के दबाव में आपने तेज़ी से फ़ैसला किया ({speed['under_time_pressure_median_s']}s), जबकि दबाव के बिना ({speed['without_time_pressure_median_s']}s)।"}[lang])
    vp, vn = ev_usage["verification_rate_under_time_pressure"], ev_usage["verification_rate_without_time_pressure"]
    if vp is not None and vn is not None and vp < vn:
        insights.append({"en": "You were less likely to verify claims when urgency or a countdown was introduced.",
                         "hinglish": "Jab jaldi ya countdown aaya to aap claims ko verify karne mein kam rahe.",
                         "hi": "जब जल्दबाज़ी या काउंटडाउन आया तो आप दावों को सत्यापित करने में कम रहे।"}[lang])
    if nxt.get("scenario"):
        insights.append(nxt["scenario"]["rationale"])
    return {"fingerprint": fp, "recognized": pack(recognized), "missed": pack(missed), "behaviours": behaviours, "misconceptions": misconceptions,
            "concept_mastery": concepts, "scenario_performance": performance, "decision_speed": speed, "evidence_usage": ev_usage,
            "recommended_training": nxt, "improvement": impr, "insights": insights, "totals": {"decisions": len(decisions), "scenarios_completed": len(sess_list)},
            "generated_from": "your recorded decisions only; nothing is estimated or pre-filled"}


def dashboard(db: Session, user: m.User, lang: str) -> dict:
    lang = lang_of(lang)
    sess_all = list(db.scalars(select(m.ScenarioSession).where(m.ScenarioSession.user_id == user.id)))
    completed = [s for s in sess_all if s.status == "completed"]
    scenarios = load_scenarios()
    loc = {sid: eng.localize(sc, lang) for sid, sc in scenarios.items()}
    mastered = [r for r in db.scalars(select(m.UserConcept).where(m.UserConcept.user_id == user.id)) if r.mastery >= 0.8]
    misc = list(db.scalars(select(m.UserMisconception).where(m.UserMisconception.user_id == user.id)))
    recent = list(db.scalars(select(m.ScenarioDecision).where(m.ScenarioDecision.user_id == user.id).order_by(m.ScenarioDecision.id.desc()).limit(8)))
    recent_out = []
    for d in recent:
        s = db.get(m.ScenarioSession, d.session_id)
        sc = loc.get(s.scenario_id) if s else None
        st = sc.states.get(d.state_key) if sc else None
        act = next((a.label for a in st.actions if a.id == d.action_id), d.action_id) if st else d.action_id
        recent_out.append({"scenario": sc.title if sc else "", "situation": st.title if st else d.state_key, "action": act, "quality": d.action_quality,
                           "latency_s": None if d.latency_ms is None else round(d.latency_ms / 1000, 1), "at": d.created_at.isoformat()})
    fp = scoring.fingerprint_view(db, user.id, lang)
    nxt = sessions.recommend_next(db, user, lang, persist=False)
    played = {s.scenario_id for s in completed}
    return {"user": {"display_name": user.display_name, "streak_days": user.streak_days, "is_demo": user.is_demo},
            "fingerprint": fp, "scenarios_completed": len(completed), "scenarios_total": len(scenarios), "scenarios_played_ids": sorted(played),
            "concepts_mastered": len(mastered), "concepts_total": len(load_concepts()),
            "misconceptions_resolved": sum(1 for r in misc if r.status == "resolved"), "misconceptions_active": sum(1 for r in misc if r.status != "resolved"),
            "streak_days": user.streak_days, "recent_decisions": recent_out, "improvement": improvement(db, user.id, lang),
            "recommendation": nxt, "outcomes": dict(Counter((s.summary or {}).get("outcome", {}).get("kind", "?") for s in completed))}
