"""Idempotent sync of static content (concepts, misconceptions, scenarios, lessons, quizzes, simulations) into the DB."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.misconception.taxonomy import MISCONCEPTIONS
from ai.scenario_engine.engine import content_hash, localize
from apps.api.services.content import load_concepts, load_scenarios
from database import models as m
from simulations.engine import REGISTRY as SIMS

log = logging.getLogger("arth.seed")
LANGS = ("en", "hinglish", "hi")


def sync_content(db: Session) -> dict[str, int]:
    counts = {"concepts": 0, "misconceptions": 0, "scenarios": 0, "lessons": 0, "quiz": 0, "simulations": 0}
    for c in load_concepts():
        row = db.get(m.Concept, c["id"])
        content = {k: v for k, v in c.items() if k not in ("id", "category", "quiz")}
        content["name"] = c["name"]
        if row is None:
            db.add(m.Concept(id=c["id"], name=c["name"]["en"], category=c["category"], content=content))
        else:
            row.name, row.category, row.content = c["name"]["en"], c["category"], content
        counts["concepts"] += 1
    db.flush()
    for c in load_concepts():
        for q in c["quiz"]:
            row = db.get(m.QuizQuestion, q["id"])
            payload = {k: v for k, v in q.items() if k not in ("id", "difficulty")}
            if row is None:
                db.add(m.QuizQuestion(id=q["id"], concept_id=c["id"], difficulty=q["difficulty"], content=payload))
            else:
                row.concept_id, row.difficulty, row.content = c["id"], q["difficulty"], payload
            counts["quiz"] += 1
    for mi in MISCONCEPTIONS:
        row = db.get(m.Misconception, mi["id"])
        content = {k: mi[k] for k in ("description", "correction", "concept")}
        if row is None:
            db.add(m.Misconception(id=mi["id"], name=mi["name"], content=content))
        else:
            row.name, row.content = mi["name"], content
        counts["misconceptions"] += 1
    db.flush()  # misconceptions must exist before lessons reference them (no ORM relationship orders these inserts)
    for mi in MISCONCEPTIONS:
        lid = f"misc_{mi['id']}"
        lc = {lang: {"title": mi["name"], "body": mi["correction"][lang]} for lang in LANGS}
        lrow = db.get(m.Lesson, lid)
        if lrow is None:
            db.add(m.Lesson(id=lid, concept_id=mi["concept"], misconception_id=mi["id"], kind="misconception", title=mi["name"], content=lc))
        else:
            lrow.content, lrow.title = lc, mi["name"]
        counts["lessons"] += 1
    db.flush()
    for sc in load_scenarios().values():
        h = content_hash(sc)
        row = db.get(m.Scenario, sc.id)
        data = sc.model_dump()
        if row is None:
            row = m.Scenario(id=sc.id, title=sc.title, difficulty=sc.difficulty, version=sc.version, concept_tags=sc.concept_tags,
                             pressure_tags=sc.pressure_tags, definition=data, content_hash=h)
            db.add(row)
            db.flush()
        elif row.content_hash != h:
            row.title, row.difficulty, row.version = sc.title, sc.difficulty, row.version + 1
            row.concept_tags, row.pressure_tags, row.definition, row.content_hash = sc.concept_tags, sc.pressure_tags, data, h
        existing = {s.state_key: s for s in db.scalars(select(m.ScenarioState).where(m.ScenarioState.scenario_id == sc.id))}
        for key, st in sc.states.items():
            if key in existing:
                existing[key].is_terminal, existing[key].definition = st.terminal, st.model_dump()
            else:
                db.add(m.ScenarioState(scenario_id=sc.id, state_key=key, is_terminal=st.terminal, definition=st.model_dump()))
        for key in set(existing) - set(sc.states):
            db.delete(existing[key])
        counts["scenarios"] += 1
        ml = sc.reflection.micro_lesson
        lc = {}
        for lang in LANGS:
            loc = localize(sc, lang)
            lc[lang] = {"title": loc.reflection.micro_lesson.title, "body": loc.reflection.micro_lesson.body}
        lid = f"{sc.id}_micro"
        lrow = db.get(m.Lesson, lid)
        if lrow is None:
            db.add(m.Lesson(id=lid, concept_id=ml.concept_id, kind="micro", title=ml.title, content=lc))
        else:
            lrow.concept_id, lrow.title, lrow.content = ml.concept_id, ml.title, lc
        counts["lessons"] += 1
    term = ["nav", "sip", "etf", "bond", "mutual_fund", "financial_disclosures", "fees"]
    lrow = db.get(m.Lesson, "terminology_micro_lessons")
    tcontent = {"concepts": term, **{lang: {"title": {"en": "Key terms in plain language", "hinglish": "Zaroori shabd saral bhasha mein", "hi": "ज़रूरी शब्द सरल भाषा में"}[lang],
                                              "body": ""} for lang in LANGS}}
    if lrow is None:
        db.add(m.Lesson(id="terminology_micro_lessons", concept_id="financial_disclosures", kind="terminology", title="Key terms in plain language", content=tcontent))
    else:
        lrow.content = tcontent
    counts["lessons"] += 1
    for sid, spec in SIMS.items():
        row = db.get(m.Simulation, sid)
        definition = {"params": spec["params"], "blurb": spec["blurb"]}
        if row is None:
            db.add(m.Simulation(id=sid, name=spec["name"], concept_tags=spec["concepts"], definition=definition))
        else:
            row.name, row.concept_tags, row.definition = spec["name"], spec["concepts"], definition
        counts["simulations"] += 1
    db.commit()
    log.info("content synced: %s", counts)
    return counts
