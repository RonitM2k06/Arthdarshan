from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.deps import current_user, language
from apps.api.schemas.core import DecisionIn, StartSession
from apps.api.services import reports, sessions
from apps.api.services.content import load_scenarios
from database import models as m
from database.session import get_db

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])
decisions_router = APIRouter(prefix="/api/decisions", tags=["decisions"])
reflection_router = APIRouter(prefix="/api/reflection", tags=["reflection"])


@router.get("", summary="List scenarios with your progress")
def list_scenarios(user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    done = {}
    for s in db.scalars(select(m.ScenarioSession).where(m.ScenarioSession.user_id == user.id, m.ScenarioSession.status == "completed")):
        o = (s.summary or {}).get("outcome", {}).get("kind")
        rec = done.setdefault(s.scenario_id, {"plays": 0, "best": None, "last": None})
        rec["plays"] += 1
        rec["last"] = o
        order = {"safe": 2, "mixed": 1, "unsafe": 0}
        if rec["best"] is None or order.get(o, -1) > order.get(rec["best"], -1):
            rec["best"] = o
    rec_next = sessions.recommend_next(db, user, lang, persist=False)
    out = []
    for sid, sc in load_scenarios().items():
        card = sessions.scenario_card(sc, lang)
        card["progress"] = done.get(sid, {"plays": 0, "best": None, "last": None})
        card["recommended"] = bool(rec_next.get("scenario") and rec_next["scenario"]["id"] == sid)
        out.append(card)
    out.sort(key=lambda c: (c["id"] != "guaranteed_opportunity", c["difficulty"], c["title"]))
    return {"scenarios": out, "recommendation": rec_next, "disclaimer": "SIMULATED · NO REAL MONEY · FICTIONAL SCENARIOS"}


@router.get("/{scenario_id}", summary="Scenario card")
def get_scenario(scenario_id: str, lang: str = Depends(language), user: m.User = Depends(current_user)):
    return sessions.scenario_card(sessions.get_scenario(scenario_id), lang)


@router.post("/start", summary="Start a scenario session")
def start(body: StartSession, user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    return sessions.start_session(db, user, body.scenario_id, lang, body.selection_id)


@router.get("/sessions/{session_id}", summary="Resume or review a session")
def resume(session_id: str, user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    return sessions.resume_session(db, user, session_id, lang)


@router.post("/sessions/{session_id}/abandon")
def abandon(session_id: str, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    sessions.abandon_session(db, user, session_id)
    return {"status": "abandoned"}


@decisions_router.post("", summary="Submit a decision (action + reasoning + confidence + evidence noticed)")
def decide(body: DecisionIn, user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    return sessions.decide(db, user, body, lang)


@decisions_router.get("/history", summary="Recent decisions")
def history(user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    return {"decisions": reports.dashboard(db, user, lang)["recent_decisions"]}


@reflection_router.get("/{session_id}", summary="Reflection and analysis for a completed scenario")
def reflection(session_id: str, user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    sess = sessions._own(db, user, session_id)
    if sess.status != "completed":
        return {"status": sess.status, "summary": None}
    return {"status": "completed", "summary": sess.summary}
