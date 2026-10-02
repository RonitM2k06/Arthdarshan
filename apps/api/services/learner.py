"""Learner-state helpers: concepts (BKT), misconception tracking, streaks, and the adaptive-policy input state."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.adaptive_learning import mastery
from ai.adaptive_learning.policy import UserState
from apps.api.services import scoring
from database import models as m


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def touch_streak(user: m.User) -> None:
    today = date.today().isoformat()
    if user.last_active_date == today:
        return
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    user.streak_days = (user.streak_days or 0) + 1 if user.last_active_date == yesterday else 1
    user.last_active_date = today


def update_concepts(db: Session, user_id: int, concept_ids: list[str], outcome: str) -> None:
    for cid in dict.fromkeys(concept_ids):
        if db.get(m.Concept, cid) is None:
            continue
        row = db.scalar(select(m.UserConcept).where(m.UserConcept.user_id == user_id, m.UserConcept.concept_id == cid))
        if row is None:
            row = m.UserConcept(user_id=user_id, concept_id=cid, mastery=mastery.DEFAULT.p_init, attempts=0, correct=0)
            db.add(row)
        row.mastery = mastery.update(row.mastery, outcome)
        row.attempts += 1
        row.correct += 1 if outcome == "safe" else 0


def record_detection(db: Session, user_id: int, mid: str) -> None:
    row = db.scalar(select(m.UserMisconception).where(m.UserMisconception.user_id == user_id, m.UserMisconception.misconception_id == mid))
    now = utcnow()
    if row is None:
        db.add(m.UserMisconception(user_id=user_id, misconception_id=mid, detections=1, exposures=0, clean_streak=0,
                                   status="active", first_seen=now, last_seen=now))
    else:
        row.detections += 1
        row.clean_streak = 0
        row.status = "active"
        row.last_seen = now


def close_exposures(db: Session, user_id: int, tested: list[str], detected_in_session: set[str]) -> list[str]:
    """After a scenario: for each tested misconception previously detected, record whether it re-appeared."""
    newly_resolved: list[str] = []
    for mid in tested:
        row = db.scalar(select(m.UserMisconception).where(m.UserMisconception.user_id == user_id, m.UserMisconception.misconception_id == mid))
        if row is None:
            continue
        row.exposures += 1
        if mid in detected_in_session:
            row.clean_streak = 0
            row.status = "active"
            continue
        row.clean_streak += 1
        if row.clean_streak >= 2:
            if row.status != "resolved":
                newly_resolved.append(mid)
            row.status = "resolved"
        elif row.detections > 0:
            row.status = "improving"
    return newly_resolved


def build_user_state(db: Session, user_id: int) -> UserState:
    fp = scoring.compute_fingerprint(db, user_id)
    dims = {d: (v["score"], v["n"]) for d, v in fp.items() if v["score"] is not None}
    conc = {r.concept_id: r.mastery for r in db.scalars(select(m.UserConcept).where(m.UserConcept.user_id == user_id))}
    misc = {r.misconception_id: {"detections": r.detections, "status": r.status, "clean_streak": r.clean_streak}
            for r in db.scalars(select(m.UserMisconception).where(m.UserMisconception.user_id == user_id))}
    sessions = db.scalars(select(m.ScenarioSession).where(m.ScenarioSession.user_id == user_id, m.ScenarioSession.status == "completed")
                          .order_by(m.ScenarioSession.completed_at)).all()
    completed = [(s.scenario_id, (s.summary or {}).get("outcome", {}).get("kind", "mixed")) for s in sessions]
    return UserState(dimension_scores=dims, concept_mastery=conc, misconceptions=misc, completed=completed)
