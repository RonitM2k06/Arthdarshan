from __future__ import annotations

import base64
import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ai.llm import client as llm
from ai.misconception import ml_models
from ai.rag import engine as rag
from ai.safety.gateway import check_input, check_output
from ai.voice import stt, tts
from apps.api.config import get_settings
from apps.api.deps import current_user, language
from apps.api.errors import AppError
from apps.api.schemas.core import AskIn, SafetyCheckIn, VoiceTTSIn
from apps.api.services.content import load_concepts, load_scenarios
from database import models as m
from database.session import get_db

log = logging.getLogger("arth.ai_router")
rag_router = APIRouter(prefix="/api/rag", tags=["rag"])
voice_router = APIRouter(prefix="/api/voice", tags=["voice"])
models_router = APIRouter(prefix="/api/models", tags=["models"])
health_router = APIRouter(prefix="/api/health", tags=["health"])
safety_router = APIRouter(prefix="/api/safety", tags=["safety"])


def ask_pipeline(db: Session, question: str, lang: str) -> dict:
    """USER INPUT -> SAFETY -> RAG/LLM -> OUTPUT CHECK -> SAFE RESPONSE (shared by text and voice)."""
    guard = check_input(question, lang)
    if not guard.allowed:
        detected = rag.detect_language(question, lang)
        reply = guard.message if detected == lang else check_input(question, detected).message
        return {"answer": reply, "language": detected, "citations": [], "grounded": False, "blocked": True, "safety": guard.to_dict(), "source": "safety_gateway"}
    res = rag.answer(db, guard.text, lang)
    out = check_output(res["answer"], res["language"], cited=bool(res["citations"]))
    if not out.allowed:
        res.update(answer=out.text, grounded=False, citations=[], source="safety_rewrite")
    res.update(blocked=False, safety=guard.to_dict())
    return res


@rag_router.post("/ask", summary="Grounded educational Q&A with citations")
def ask(body: AskIn, user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    return ask_pipeline(db, body.question, body.language or lang)


@rag_router.get("/documents", summary="What the knowledge base contains and where it came from")
def documents(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    docs = db.scalars(select(m.KnowledgeDocument).order_by(m.KnowledgeDocument.title)).all()
    return {"documents": [{"key": d.doc_key, "title": d.title, "source": d.source, "source_type": d.source_type, "verified_official": d.verified_official,
                           "date": d.published_date, "language": d.language, "chunks": len(d.chunks)} for d in docs],
            "retrieval": "hybrid (embeddings + BM25)" if rag.embedder_status().get("loaded") else "keyword (BM25)"}


@rag_router.post("/ingest", summary="Re-read data/knowledge_base and data/raw (local admin action)")
def ingest(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    return rag.ingest(db, with_embeddings=False)


@safety_router.post("/check", summary="Run text through the Safety Gateway (used by the demo)")
def safety_check(body: SafetyCheckIn, user: m.User = Depends(current_user), lang: str = Depends(language)):
    res = check_input(body.text, lang) if body.direction == "input" else check_output(body.text, lang)
    return res.to_dict() | {"text": res.text}


@voice_router.get("/status")
def voice_status(user: m.User = Depends(current_user)):
    return {"stt": stt.status(), "tts": tts.status(), "browser_fallback": True,
            "note": "If a local engine is unavailable the app falls back to your browser's speech features, then to plain text."}


@voice_router.post("/transcribe", summary="Local speech-to-text")
async def transcribe(audio: UploadFile = File(...), language_hint: str = Form("en"), user: m.User = Depends(current_user)):
    data = await audio.read()
    suffix = "." + (audio.filename or "a.webm").rsplit(".", 1)[-1][:5]
    try:
        out = stt.transcribe(data, language_hint, suffix)
    except ValueError as exc:
        raise AppError(400, "bad_audio", str(exc)) from exc
    except RuntimeError as exc:
        raise AppError(503, "stt_unavailable", f"Local speech recognition is unavailable ({exc}). Please type your answer or use browser speech.") from exc
    return out


@voice_router.post("/tts", summary="Local text-to-speech (WAV)")
def speak(body: VoiceTTSIn, user: m.User = Depends(current_user)):
    safe = check_output(body.text, body.language)
    try:
        wav = tts.synthesize(safe.text if safe.action == "rewrite" else body.text, body.language)
    except RuntimeError as exc:
        raise AppError(503, "tts_unavailable", f"Local voice is unavailable ({exc}). Your browser's speech synthesis will be used instead.") from exc
    return Response(content=wav, media_type="audio/wav")


@voice_router.post("/ask", summary="Voice or text question -> grounded spoken answer")
async def voice_ask(audio: UploadFile | None = File(default=None), question: str = Form(""), language_hint: str = Form("en"), speak_answer: bool = Form(True),
                    user: m.User = Depends(current_user), lang: str = Depends(language), db: Session = Depends(get_db)):
    transcript, fallbacks = question.strip(), []
    if audio is not None and not transcript:
        data = await audio.read()
        try:
            transcript = stt.transcribe(data, language_hint)["text"]
        except Exception as exc:  # noqa: BLE001
            raise AppError(503, "stt_unavailable", f"Could not transcribe locally ({exc}). Please type the question or use browser speech.") from exc
    if not transcript:
        raise AppError(400, "empty_question", "Say or type a question first.")
    transcript = transcript[:500]
    res = ask_pipeline(db, transcript, language_hint if language_hint != "en" else lang)
    out = {"transcript": transcript, **res, "audio_base64": None, "fallbacks": fallbacks}
    if speak_answer:
        try:
            out["audio_base64"] = base64.b64encode(tts.synthesize(res["answer"], res["language"])).decode()
        except RuntimeError:
            fallbacks.append("tts_unavailable: use browser speech synthesis or read the text")
    return out


@models_router.get("", summary="Local AI/ML components and trained model versions")
def models(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    versions = db.scalars(select(m.ModelVersion).order_by(m.ModelVersion.created_at.desc())).all()
    runs = db.scalars(select(m.TrainingRun).order_by(m.TrainingRun.started_at.desc()).limit(10)).all()
    return {"components": component_status(),
            "model_versions": [{"name": v.name, "version": v.version, "kind": v.kind, "data_version": v.data_version, "synthetic_data": v.synthetic_data,
                                "metrics": v.metrics, "active": v.active, "created_at": v.created_at.isoformat()} for v in versions],
            "training_runs": [{"model": r.model_name, "status": r.status, "data_version": r.data_version, "metrics": r.metrics, "started_at": r.started_at.isoformat()} for r in runs]}


def component_status() -> dict:
    s = get_settings()
    return {"llm": llm.status(), "embeddings": rag.embedder_status(), "stt": stt.status(), "tts": tts.status(),
            "ml": {n: ml_models.available(n) for n in ("misconception_clf", "behaviour_clf", "success_model")},
            "low_resource": s.low_resource}


@health_router.get("", summary="Health check (never fails because an optional AI component is down)")
def health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": "ok" if db_ok else "unavailable", "scenarios": len(load_scenarios()),
            "concepts": len(load_concepts()), "components": component_status(), "offline_core": True,
            "safety": "rule-based gateway active (no model required)"}
