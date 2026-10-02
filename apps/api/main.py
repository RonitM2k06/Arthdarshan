"""ARTHDARSHAN API.  Run:  uvicorn apps.api.main:app --port 8000

Everything runs locally. The core simulator needs no internet, no LLM, no GPU and no model download.
"""
from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api import errors
from apps.api.config import get_settings
from apps.api.logging_conf import setup_logging
from apps.api.routers import ai_system, auth_users, learning, scenarios
from apps.api.services.seed import sync_content
from database import session as dbs

log = logging.getLogger("arth.main")


def _background_embeddings() -> None:
    """Compute chunk embeddings after startup so the first request is never blocked by model loading."""
    try:
        from ai.rag import engine as rag
        with dbs.session_scope() as db:
            rag.ingest(db, with_embeddings=True)
        log.info("background embedding ingest finished")
    except Exception as exc:  # noqa: BLE001
        log.warning("background embedding ingest skipped: %s", type(exc).__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    s = get_settings()
    dbs.init_engine(s.database_url)
    if s.auto_migrate:
        dbs.run_migrations(s.database_url)
    with dbs.session_scope() as db:
        sync_content(db)
        from ai.rag import engine as rag
        rag.ingest(db, with_embeddings=False)
    if s.enable_embeddings and not s.low_resource:
        threading.Thread(target=_background_embeddings, name="embed-ingest", daemon=True).start()
    if s.llm_active:
        from ai.llm import client as llm_client
        threading.Thread(target=llm_client.warmup, name="llm-warmup", daemon=True).start()
    log.info("ARTHDARSHAN ready (llm=%s, low_resource=%s)", s.llm_active, s.low_resource)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="ARTHDARSHAN API", version="1.0.0", lifespan=lifespan,
                  description="Financial decision-resilience simulator. Educational only: no investment advice, no real money.")
    app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins, allow_methods=["*"], allow_headers=["*"], allow_credentials=False)
    errors.install(app)
    app.include_router(auth_users.auth_router)
    app.include_router(auth_users.users_router)
    app.include_router(scenarios.router)
    app.include_router(scenarios.decisions_router)
    app.include_router(scenarios.reflection_router)
    app.include_router(learning.sim_router)
    app.include_router(learning.learning_router)
    app.include_router(learning.concepts_router)
    app.include_router(learning.progress_router)
    app.include_router(learning.resilience_router)
    app.include_router(ai_system.rag_router)
    app.include_router(ai_system.voice_router)
    app.include_router(ai_system.models_router)
    app.include_router(ai_system.health_router)
    app.include_router(ai_system.safety_router)
    return app


app = create_app()
