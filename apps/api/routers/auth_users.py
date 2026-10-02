from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from apps.api.deps import current_user, hash_token, new_token
from apps.api.schemas.core import AuthOut, AuthStart, UserOut, UserUpdate
from database import models as m
from database.session import get_db

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])
users_router = APIRouter(prefix="/api/users", tags=["users"])


def _create(db: Session, body: AuthStart, demo: bool = False) -> AuthOut:
    token = new_token()
    user = m.User(public_id=str(uuid.uuid4()), display_name=(body.display_name or None), token_hash=hash_token(token),
                  language=body.language, simple_mode=body.simple_mode, is_demo=demo)
    db.add(user)
    db.commit()
    return AuthOut(token=token, user=UserOut.model_validate(user))


@auth_router.post("/start", response_model=AuthOut, summary="Start an anonymous local learner profile (no email, no password)")
def start(body: AuthStart, db: Session = Depends(get_db)):
    return _create(db, body)


@auth_router.post("/demo", response_model=AuthOut, summary="Start a fresh demo profile")
def demo(body: AuthStart | None = None, db: Session = Depends(get_db)):
    body = body or AuthStart(display_name="Demo learner")
    if not body.display_name:
        body.display_name = "Demo learner"
    return _create(db, body, demo=True)


@users_router.get("/me", response_model=UserOut)
def me(user: m.User = Depends(current_user)):
    return user


@users_router.patch("/me", response_model=UserOut)
def update_me(body: UserUpdate, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    return user


def _wipe(db: Session, user_id: int) -> dict[str, int]:
    counts = {}
    # sessions first (cascades decisions + reasoning); then rows that session rows referenced
    for name, model, col in [("sessions", m.ScenarioSession, m.ScenarioSession.user_id), ("selections", m.AdaptiveSelection, m.AdaptiveSelection.user_id),
                             ("observations", m.DimensionObservation, m.DimensionObservation.user_id), ("scores", m.ResilienceScore, m.ResilienceScore.user_id),
                             ("concepts", m.UserConcept, m.UserConcept.user_id), ("misconceptions", m.UserMisconception, m.UserMisconception.user_id),
                             ("quiz_attempts", m.QuizAttempt, m.QuizAttempt.user_id), ("simulation_events", m.SimulationEvent, m.SimulationEvent.user_id)]:
        counts[name] = db.execute(delete(model).where(col == user_id)).rowcount or 0
    return counts


@users_router.delete("/me/data", summary="Delete all learning data for this profile (keeps the profile itself)")
def reset_data(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    counts = _wipe(db, user.id)
    user.streak_days, user.last_active_date = 0, None
    db.commit()
    return {"deleted": counts, "profile_kept": True}


@users_router.delete("/me", summary="Delete this profile and everything stored about it")
def delete_me(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    counts = _wipe(db, user.id)
    db.delete(user)
    db.commit()
    return {"deleted": counts, "profile_kept": False}


@users_router.get("/me/export", summary="Export everything stored about this profile")
def export_me(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    def rows(model, col):
        return [{c.name: (getattr(r, c.name).isoformat() if hasattr(getattr(r, c.name), "isoformat") else getattr(r, c.name))
                 for c in model.__table__.columns if c.name not in ("token_hash", "embedding")} for r in db.scalars(select(model).where(col == user.id))]
    return {"profile": UserOut.model_validate(user).model_dump(mode="json"),
            "decisions": rows(m.ScenarioDecision, m.ScenarioDecision.user_id), "sessions": rows(m.ScenarioSession, m.ScenarioSession.user_id),
            "observations": rows(m.DimensionObservation, m.DimensionObservation.user_id), "scores": rows(m.ResilienceScore, m.ResilienceScore.user_id),
            "concepts": rows(m.UserConcept, m.UserConcept.user_id), "misconceptions": rows(m.UserMisconception, m.UserMisconception.user_id),
            "quiz_attempts": rows(m.QuizAttempt, m.QuizAttempt.user_id), "simulation_events": rows(m.SimulationEvent, m.SimulationEvent.user_id),
            "note": "This is everything ARTHDARSHAN stores about you. It stays on this device."}
