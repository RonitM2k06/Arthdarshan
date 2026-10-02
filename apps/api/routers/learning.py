from __future__ import annotations

import random

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.misconception import detector
from ai.misconception.evidence_lab import SAMPLES, analyze
from ai.safety.gateway import check_input
from apps.api.deps import current_user, language
from apps.api.errors import AppError
from apps.api.schemas.core import AskIn, QuizAnswerIn, SimRunIn
from apps.api.services import learner, reports, scoring, sessions
from apps.api.services.content import load_concepts
from database import models as m
from database.session import get_db
from simulations import engine as sim

learning_router = APIRouter(prefix="/api/learning", tags=["learning"])
concepts_router = APIRouter(prefix="/api/concepts", tags=["concepts"])
sim_router = APIRouter(prefix="/api/simulations", tags=["simulations"])
progress_router = APIRouter(prefix="/api/progress", tags=["progress"])
resilience_router = APIRouter(prefix="/api/resilience", tags=["resilience"])


def _concept_view(c: dict, lang: str) -> dict:
    return {"id": c["id"], "name": c["name"][lang], "category": c["category"], "simple": c["simple"][lang], "simple_en": c["simple"]["en"],
            "detailed": c["detailed"], "examples": c["examples"], "related": c["related"], "misconceptions": c["misconceptions"],
            "scenarios": c["scenarios"], "simulation": c.get("simulation"), "quiz_count": len(c["quiz"])}


@concepts_router.get("", summary="The concept graph (nodes, edges and your mastery)")
def graph(user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    mastery = {r.concept_id: r.mastery for r in db.scalars(select(m.UserConcept).where(m.UserConcept.user_id == user.id))}
    cs = load_concepts()
    nodes = [{"id": c["id"], "name": c["name"][lang], "category": c["category"], "simple": c["simple"][lang], "mastery": round(mastery[c["id"]], 2) if c["id"] in mastery else None} for c in cs]
    edges = sorted({tuple(sorted((c["id"], r))) for c in cs for r in c["related"]})
    return {"nodes": nodes, "edges": [{"a": a, "b": b} for a, b in edges]}


@concepts_router.get("/{concept_id}")
def concept(concept_id: str, user: m.User = Depends(current_user), lang: str = Depends(language)):
    c = next((x for x in load_concepts() if x["id"] == concept_id), None)
    if c is None:
        raise AppError(404, "concept_not_found", "Unknown concept.")
    view = _concept_view(c, lang)
    view["misconception_details"] = [detector.correction(i, lang) for i in c["misconceptions"]]
    return view


@learning_router.get("/recommendation", summary="Transparent next-training recommendation")
def recommendation(user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    return sessions.recommend_next(db, user, lang, persist=False)


@learning_router.get("/lessons")
def lessons(concept: str | None = None, user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    q = select(m.Lesson)
    if concept:
        q = q.where(m.Lesson.concept_id == concept)
    out = []
    for l in db.scalars(q):
        c = l.content.get(lang) or l.content.get("en") or {}
        out.append({"id": l.id, "kind": l.kind, "concept_id": l.concept_id, "misconception_id": l.misconception_id, "title": c.get("title", l.title), "body": c.get("body", ""),
                    "concepts": l.content.get("concepts")})
    return {"lessons": out}


@learning_router.get("/quiz")
def quiz(concept: str | None = None, n: int = Query(default=3, ge=1, le=10), user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    q = select(m.QuizQuestion)
    if concept:
        q = q.where(m.QuizQuestion.concept_id == concept)
    pool = list(db.scalars(q))
    if not pool:
        raise AppError(404, "no_questions", "No quiz questions for that concept.")
    if not concept:  # adaptive: weakest concepts first
        mastery = {r.concept_id: r.mastery for r in db.scalars(select(m.UserConcept).where(m.UserConcept.user_id == user.id))}
        pool.sort(key=lambda x: mastery.get(x.concept_id, 0.2))
        pool = pool[: max(n * 2, n)]
        random.Random(len(mastery)).shuffle(pool)
    out = []
    for qq in pool[:n]:
        out.append({"id": qq.id, "concept_id": qq.concept_id, "difficulty": qq.difficulty, "question": qq.content["question"],
                    "options": [o["text"] for o in qq.content["options"]]})
    return {"questions": out}


@learning_router.post("/quiz/answer")
def quiz_answer(body: QuizAnswerIn, user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    q = db.get(m.QuizQuestion, body.question_id)
    if q is None:
        raise AppError(404, "question_not_found", "Unknown question.")
    opts = q.content["options"]
    if body.selected_index >= len(opts):
        raise AppError(400, "invalid_option", "That option does not exist.")
    correct = body.selected_index == q.content["correct_index"]
    mid = opts[body.selected_index].get("misconception_id")
    db.add(m.QuizAttempt(user_id=user.id, question_id=q.id, selected_index=body.selected_index, correct=correct, misconception_id=mid, latency_ms=body.latency_ms))
    learner.update_concepts(db, user.id, [q.concept_id], "safe" if correct else "unsafe")
    scoring.store_observations(db, user.id, "quiz", q.id, [scoring.observation_for_quiz(q.concept_id, correct)])
    mis = None
    if mid and not correct:
        learner.record_detection(db, user.id, mid)
        mis = detector.correction(mid, lang)
    learner.touch_streak(user)
    db.commit()
    row = db.scalar(select(m.UserConcept).where(m.UserConcept.user_id == user.id, m.UserConcept.concept_id == q.concept_id))
    return {"correct": correct, "correct_index": q.content["correct_index"], "explanation": q.content["explanation"], "misconception": mis,
            "mastery": round(row.mastery, 2) if row else None}


@learning_router.get("/evidence-lab/samples")
def lab_samples():
    return {"samples": SAMPLES, "disclaimer": "FICTIONAL EXAMPLES"}


@learning_router.post("/evidence-lab/analyze")
def lab_analyze(body: AskIn, user: m.User = Depends(current_user), lang: str = Depends(language)):
    safety = check_input(body.question, lang)
    text = safety.text  # sensitive values already redacted; advice-seeking in a *pasted claim* is fine to analyse
    res = analyze(text, body.language or lang)
    res["safety"] = {"redactions": safety.redactions, "message": safety.message if safety.redactions else None}
    return res


@sim_router.get("", summary="Catalogue of consequence simulations (illustrative, no real money)")
def sim_catalog(user: m.User = Depends(current_user)):
    return {"simulations": sim.catalog(), "label": sim.LABEL}


@sim_router.post("/{sim_id}/run")
def sim_run(sim_id: str, body: SimRunIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        res = sim.run(sim_id, body.params)
    except sim.SimulationError as exc:
        raise AppError(422, "invalid_simulation", str(exc)) from exc
    db.add(m.SimulationEvent(user_id=user.id, simulation_id=sim_id, params=res["params"], result_summary=res["summary"]))
    db.commit()
    return res


@progress_router.get("", summary="Educational dashboard data")
def progress(user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    return reports.dashboard(db, user, lang)


@resilience_router.get("", summary="Financial Resilience Fingerprint")
def fingerprint(user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    return scoring.fingerprint_view(db, user.id, lang)


@resilience_router.get("/report", summary="Full resilience report from your recorded interactions")
def report(user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    return reports.build_report(db, user, lang)


@resilience_router.get("/history")
def history(user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    return reports.improvement(db, user.id, lang)
