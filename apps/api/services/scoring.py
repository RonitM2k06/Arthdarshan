"""Financial Resilience Fingerprint: scores derived ONLY from recorded interaction data.

Per decision we emit explicit observations (dimension, value 0-100, weight, note). A dimension's score is a
recency-weighted average with a weak prior of 50 (weight 1). A dimension with no observations is reported as
"not yet measured" (score None) instead of inventing a number. The rules are documented in docs/ML.md and
docs/SCENARIO_ENGINE.md and covered by tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.adaptive_learning.dimensions import DIMS, lang_of, name as dim_name
from ai.scenario_engine.engine import StepResult
from ai.scenario_engine.schema import DIMENSIONS, Scenario, State
from database import models as m

Q_VALUE = {"safe": 90.0, "mixed": 55.0, "unsafe": 15.0}
PRIOR = 50.0
PRIOR_WEIGHT = 1.0
DECAY = 0.9

PRESSURE_DIM = {
    "urgency": "fomo_resistance", "countdown": "fomo_resistance", "scarcity": "fomo_resistance", "fomo": "fomo_resistance",
    "social_proof": "herd_resistance", "peer_pressure": "herd_resistance",
    "fear": "emotional_discipline", "greed": "emotional_discipline", "loss_recovery": "emotional_discipline",
    "emotional_story": "emotional_discipline", "authority": "evidence_verification",
}
TERMINOLOGY_CONCEPTS = {"nav", "sip", "etf", "bond", "mutual_fund", "stock", "kyc", "financial_disclosures", "nomination"}
POSITIVE_REASONING = {"independent_reasoning", "evidence_seeking"}
NEGATIVE_REASONING = {"social_proof_reliance", "friend_reliance", "authority_reliance"}


@dataclass
class Obs:
    dimension: str
    value: float
    weight: float
    note: str


def observations_for_decision(scenario: Scenario, state: State, step: StepResult, *, confidence: int | None,
                              latency_ms: int | None, behaviours: list[str], emotions: list[str],
                              uncertainty: bool, text_detections: int) -> list[Obs]:
    q = Q_VALUE[step.quality]
    obs: list[Obs] = []
    # 1) pressure response -> the dimension that pressure type trains
    by_dim: dict[str, list[tuple[float, str]]] = {}
    for p in state.pressure:
        d = PRESSURE_DIM.get(p.type)
        if d:
            by_dim.setdefault(d, []).append((p.intensity, p.type))
    for d, items in by_dim.items():
        v = q
        if step.quality == "unsafe" and latency_ms is not None and latency_ms < 4000:
            v = max(0.0, v - 10)
        inten = sum(i for i, _ in items) / len(items)
        w = min(1.5, 0.5 + 0.25 * inten + 0.15 * (len(items) - 1))
        types = ", ".join(sorted({t for _, t in items}))
        verb = {"safe": "held steady", "mixed": "partly held steady", "unsafe": "acted"}[step.quality]
        obs.append(Obs(d, v, w, f"{verb} under {types} pressure in '{state.title}'"))
    # 2) risk recognition from warning signs noticed
    rec = step.evidence.recall
    if rec is not None:
        obs.append(Obs("risk_recognition", 100 * rec * 0.7 + q * 0.3, 1.0,
                       f"noticed {len(step.evidence.noticed_red_flags)} of {len(step.evidence.red_flags)} warning signs"))
    # 3) verification behaviour
    if step.verification is True:
        obs.append(Obs("evidence_verification", 92, 1.0, "verified independently"))
    elif step.verification is False:
        obs.append(Obs("evidence_verification", 15, 1.0, "skipped available verification"))
    elif step.requests_evidence:
        obs.append(Obs("evidence_verification", 70, 0.7, "asked for evidence (from the source itself)"))
    # 4) scam awareness for scenarios that train it
    if "scam_awareness" in scenario.scoring.dimensions:
        r = rec * 100 if rec is not None else q
        obs.append(Obs("scam_awareness", 0.6 * q + 0.4 * r, 1.0, "scam-pattern recognition and response"))
    # 5) independent reasoning from the words used
    if set(behaviours) & POSITIVE_REASONING:
        obs.append(Obs("independent_reasoning", 85, 0.8, "reasoned from evidence you could examine"))
    if set(behaviours) & NEGATIVE_REASONING:
        obs.append(Obs("independent_reasoning", 20, 0.8, "relied on others' say-so as evidence"))
    elif text_detections:
        obs.append(Obs("independent_reasoning", 30, 0.5, "reasoning contained a common misconception"))
    # 6) uncertainty and confidence calibration
    if uncertainty:
        obs.append(Obs("uncertainty_awareness", 85, 0.8, "acknowledged what cannot be known"))
    if "overconfidence" in behaviours:
        obs.append(Obs("uncertainty_awareness", 20, 0.8, "expressed certainty about the unknowable"))
    if confidence is not None:
        if confidence >= 4:
            obs.append(Obs("uncertainty_awareness", 85 if step.quality == "safe" else 15 if step.quality == "unsafe" else 45, 0.5,
                           f"high confidence ({confidence}/5) on a {step.quality} choice"))
        elif confidence <= 2:
            obs.append(Obs("uncertainty_awareness", 60 if step.quality == "safe" else 50, 0.5, f"low confidence ({confidence}/5): cautious"))
    # 7) emotional discipline from stated feelings
    if set(emotions) & {"fear", "fomo", "excitement", "anger"} and step.quality != "safe":
        obs.append(Obs("emotional_discipline", 20, 0.7, "strong emotion drove the choice"))
    if "deliberate_pause" in behaviours or "calm" in emotions:
        obs.append(Obs("emotional_discipline", 85, 0.7, "paused or stayed calm"))
    # 8) scenario-declared observations (e.g. terminology checks)
    for o in step.observations:
        obs.append(Obs(o["dimension"], o["value"], 1.0, f"answered a {o['dimension'].replace('_', ' ')} check"))
    return obs


def observation_for_quiz(concept_id: str, correct: bool) -> Obs:
    dim = "terminology" if concept_id in TERMINOLOGY_CONCEPTS else "concept_knowledge"
    return Obs(dim, 90.0 if correct else 15.0, 1.0, f"quiz on {concept_id.replace('_', ' ')}: {'correct' if correct else 'incorrect'}")


def store_observations(db: Session, user_id: int, source: str, source_id: str, obs: Iterable[Obs]) -> None:
    for o in obs:
        db.add(m.DimensionObservation(user_id=user_id, dimension=o.dimension, value=max(0.0, min(100.0, o.value)),
                                      weight=o.weight, source=source, source_id=source_id, note=o.note[:240]))


def score_from(values: list[tuple[float, float]]) -> float:
    """values: chronological (value, weight). Recency decay + weak prior."""
    n = len(values)
    num, den = PRIOR * PRIOR_WEIGHT, PRIOR_WEIGHT
    for i, (v, w) in enumerate(values):
        rw = w * (DECAY ** (n - 1 - i))
        num += rw * v
        den += rw
    return num / den


def compute_fingerprint(db: Session, user_id: int, before: datetime | None = None) -> dict[str, dict]:
    q = select(m.DimensionObservation).where(m.DimensionObservation.user_id == user_id).order_by(m.DimensionObservation.id)
    if before is not None:
        q = q.where(m.DimensionObservation.created_at <= before)
    rows = db.scalars(q).all()
    out: dict[str, dict] = {}
    for dim in DIMENSIONS:
        rs = [r for r in rows if r.dimension == dim]
        if not rs:
            out[dim] = {"score": None, "n": 0, "evidence": []}
            continue
        out[dim] = {"score": round(score_from([(r.value, r.weight) for r in rs]), 1), "n": len(rs),
                    "evidence": [{"note": r.note, "value": round(r.value)} for r in rs[-3:]][::-1]}
    return out


def snapshot(db: Session, user_id: int, session_id: str | None) -> None:
    fp = compute_fingerprint(db, user_id)
    for dim, info in fp.items():
        if info["score"] is None:
            continue
        db.add(m.ResilienceScore(user_id=user_id, dimension=dim, score=info["score"], n_observations=info["n"],
                                 session_id=session_id, evidence=info["evidence"]))


def previous_scores(db: Session, user_id: int, current_session_id: str | None = None) -> dict[str, float]:
    """Latest snapshot per dimension taken before the most recent session (for 'previous' and 'change')."""
    rows = db.scalars(select(m.ResilienceScore).where(m.ResilienceScore.user_id == user_id).order_by(m.ResilienceScore.id)).all()
    last_two: dict[str, list[float]] = {}
    for r in rows:
        last_two.setdefault(r.dimension, []).append(r.score)
    out = {}
    for dim, vals in last_two.items():
        if len(vals) >= 2:
            out[dim] = vals[-2]
    return out


def fingerprint_view(db: Session, user_id: int, lang: str = "en") -> dict:
    lang = lang_of(lang)
    fp = compute_fingerprint(db, user_id)
    prev = previous_scores(db, user_id)
    dims = []
    for dim in DIMENSIONS:
        info = fp[dim]
        p = prev.get(dim)
        dims.append({"id": dim, "name": dim_name(dim, lang), "short": DIMS[dim]["short"][lang], "score": info["score"],
                     "n_observations": info["n"], "previous": p,
                     "change": None if (p is None or info["score"] is None) else round(info["score"] - p, 1),
                     "evidence": info["evidence"], "measured": info["score"] is not None})
    measured = [d for d in dims if d["measured"] and d["n_observations"] >= 1]
    strengths, opportunities = [], []
    if measured:
        ordered = sorted(measured, key=lambda d: -d["score"])
        strengths = [d["id"] for d in ordered if d["score"] >= 65][:2]
        opportunities = [d["id"] for d in sorted(measured, key=lambda d: d["score"]) if d["score"] < 65][:2]
    texts = []
    if strengths:
        texts.append({"en": f"Your strongest area right now is {DIMS[strengths[0]]['strength']['en']}.",
                      "hinglish": f"Abhi aapka sabse mazboot kshetra hai: {DIMS[strengths[0]]['strength']['hinglish']}.",
                      "hi": f"अभी आपका सबसे मज़बूत क्षेत्र है: {DIMS[strengths[0]]['strength']['hi']}।"}[lang])
    if opportunities:
        texts.append({"en": f"Your current training opportunity is {DIMS[opportunities[0]]['opportunity']['en']}.",
                      "hinglish": f"Aapka abhi ka abhyas ka mauka hai: {DIMS[opportunities[0]]['opportunity']['hinglish']}.",
                      "hi": f"आपके अभ्यास का अभी का अवसर है: {DIMS[opportunities[0]]['opportunity']['hi']}।"}[lang])
    if not texts:
        texts.append({"en": "Play a scenario to start building your fingerprint. Every score comes from your own decisions.",
                      "hinglish": "Apna fingerprint banana shuru karne ke liye ek scenario khelo. Har score aapke apne faislon se aata hai.",
                      "hi": "अपना फ़िंगरप्रिंट बनाने के लिए एक परिदृश्य खेलें। हर स्कोर आपके अपने फ़ैसलों से आता है।"}[lang])
    return {"dimensions": dims, "strengths": strengths, "opportunities": opportunities, "summary": " ".join(texts),
            "measured_count": len(measured)}
