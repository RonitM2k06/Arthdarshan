"""SQLAlchemy models for ARTHDARSHAN. SQLite (local) is the MVP database.

Stores no financial credentials and no PII beyond an optional display name.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (JSON, Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer,
                        LargeBinary, String, Text, UniqueConstraint)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(40))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    language: Mapped[str] = mapped_column(String(12), default="en")  # en | hinglish | hi
    simple_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (CheckConstraint("language in ('en','hinglish','hi')", name="ck_user_language"),)


class Concept(Base):
    __tablename__ = "concepts"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(40), index=True)
    content: Mapped[dict] = mapped_column(JSON)  # simple/detailed/examples/i18n/related/misconceptions/scenarios


class UserConcept(Base):
    __tablename__ = "user_concepts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"))
    mastery: Mapped[float] = mapped_column(Float, default=0.2)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    __table_args__ = (UniqueConstraint("user_id", "concept_id", name="uq_user_concept"),
                      CheckConstraint("mastery >= 0 and mastery <= 1", name="ck_mastery_range"))


class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    difficulty: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer, default=1)
    concept_tags: Mapped[list] = mapped_column(JSON)
    pressure_tags: Mapped[list] = mapped_column(JSON)
    definition: Mapped[dict] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(64))
    states: Mapped[list["ScenarioState"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")


class ScenarioState(Base):
    __tablename__ = "scenario_states"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)
    state_key: Mapped[str] = mapped_column(String(60))
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False)
    definition: Mapped[dict] = mapped_column(JSON)
    scenario: Mapped[Scenario] = relationship(back_populates="states")
    __table_args__ = (UniqueConstraint("scenario_id", "state_key", name="uq_scenario_state"),)


class ScenarioSession(Base):
    __tablename__ = "scenario_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"), index=True)
    scenario_version: Mapped[int] = mapped_column(Integer, default=1)
    current_state_key: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(12), default="active")  # active | completed | abandoned
    path: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[dict | None] = mapped_column(JSON)
    selection_id: Mapped[int | None] = mapped_column(ForeignKey("adaptive_selections.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decisions: Mapped[list["ScenarioDecision"]] = relationship(back_populates="session", cascade="all, delete-orphan",
                                                                order_by="ScenarioDecision.id")
    __table_args__ = (Index("ix_session_user_status", "user_id", "status"),)


class ScenarioDecision(Base):
    __tablename__ = "scenario_decisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("scenario_sessions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    state_key: Mapped[str] = mapped_column(String(60))
    action_id: Mapped[str] = mapped_column(String(60))
    action_quality: Mapped[str] = mapped_column(String(10))  # safe | mixed | unsafe
    next_state_key: Mapped[str] = mapped_column(String(60))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[int | None] = mapped_column(Integer)
    pressure_types: Mapped[list] = mapped_column(JSON, default=list)
    countdown_expired: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence_noticed: Mapped[list] = mapped_column(JSON, default=list)
    evidence_missed: Mapped[list] = mapped_column(JSON, default=list)
    evidence_requested: Mapped[list] = mapped_column(JSON, default=list)
    analysis: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    session: Mapped[ScenarioSession] = relationship(back_populates="decisions")
    reasoning: Mapped["DecisionReasoning | None"] = relationship(back_populates="decision", uselist=False,
                                                                  cascade="all, delete-orphan")
    __table_args__ = (CheckConstraint("confidence is null or (confidence >= 1 and confidence <= 5)",
                                      name="ck_confidence_range"),)


class DecisionReasoning(Base):
    __tablename__ = "decision_reasoning"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("scenario_decisions.id", ondelete="CASCADE"), unique=True)
    text: Mapped[str] = mapped_column(Text, default="")
    safety_flags: Mapped[list] = mapped_column(JSON, default=list)
    behaviours: Mapped[list] = mapped_column(JSON, default=list)
    misconceptions: Mapped[list] = mapped_column(JSON, default=list)  # [{id, source, confidence}]
    emotional_indicators: Mapped[list] = mapped_column(JSON, default=list)
    uncertainty_recognized: Mapped[bool] = mapped_column(Boolean, default=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    explanation_source: Mapped[str] = mapped_column(String(12), default="template")  # template | llm
    decision: Mapped[ScenarioDecision] = relationship(back_populates="reasoning")


class Misconception(Base):
    __tablename__ = "misconceptions"
    id: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    content: Mapped[dict] = mapped_column(JSON)  # description, correction, i18n


class UserMisconception(Base):
    __tablename__ = "user_misconceptions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    misconception_id: Mapped[str] = mapped_column(ForeignKey("misconceptions.id"))
    detections: Mapped[int] = mapped_column(Integer, default=0)
    exposures: Mapped[int] = mapped_column(Integer, default=0)
    clean_streak: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(12), default="active")  # active | improving | resolved
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("user_id", "misconception_id", name="uq_user_misconception"),)


class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    concept_id: Mapped[str | None] = mapped_column(ForeignKey("concepts.id"), index=True)
    misconception_id: Mapped[str | None] = mapped_column(ForeignKey("misconceptions.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20), default="micro")
    title: Mapped[str] = mapped_column(String(120))
    content: Mapped[dict] = mapped_column(JSON)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[dict] = mapped_column(JSON)  # question, options[{text, misconception_id}], correct_index, explanation, i18n


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("quiz_questions.id"))
    selected_index: Mapped[int] = mapped_column(Integer)
    correct: Mapped[bool] = mapped_column(Boolean)
    misconception_id: Mapped[str | None] = mapped_column(String(8))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Simulation(Base):
    """Catalogue of consequence simulations (definitions only)."""
    __tablename__ = "simulations"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    concept_tags: Mapped[list] = mapped_column(JSON)
    definition: Mapped[dict] = mapped_column(JSON)


class SimulationEvent(Base):
    __tablename__ = "simulation_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulations.id"), index=True)
    params: Mapped[dict] = mapped_column(JSON)
    result_summary: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DimensionObservation(Base):
    """Raw evidence behind each Fingerprint dimension (value 0-100, weight>0)."""
    __tablename__ = "dimension_observations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    dimension: Mapped[str] = mapped_column(String(40))
    value: Mapped[float] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    source: Mapped[str] = mapped_column(String(20))  # decision | quiz | session
    source_id: Mapped[str | None] = mapped_column(String(40))
    note: Mapped[str | None] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (Index("ix_obs_user_dim", "user_id", "dimension"),
                      CheckConstraint("value >= 0 and value <= 100", name="ck_obs_value"))


class ResilienceScore(Base):
    __tablename__ = "resilience_scores"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    dimension: Mapped[str] = mapped_column(String(40))
    score: Mapped[float] = mapped_column(Float)
    n_observations: Mapped[int] = mapped_column(Integer)
    session_id: Mapped[str | None] = mapped_column(String(36))
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (Index("ix_score_user_dim_time", "user_id", "dimension", "created_at"),)


class AdaptiveSelection(Base):
    __tablename__ = "adaptive_selections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    weakness: Mapped[str | None] = mapped_column(String(60))
    selected_training: Mapped[str] = mapped_column(String(80))  # scenario id or simulation/lesson id
    training_kind: Mapped[str] = mapped_column(String(20), default="scenario")
    difficulty: Mapped[int | None] = mapped_column(Integer)
    rationale: Mapped[str] = mapped_column(Text)
    mastery_estimate: Mapped[float | None] = mapped_column(Float)
    predicted_success: Mapped[float | None] = mapped_column(Float)
    outcome: Mapped[str | None] = mapped_column(String(12))  # safe | mixed | unsafe once played
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), index=True)
    version: Mapped[str] = mapped_column(String(40))
    kind: Mapped[str] = mapped_column(String(30))
    path: Mapped[str] = mapped_column(String(300))
    data_version: Mapped[str] = mapped_column(String(60))
    synthetic_data: Mapped[bool] = mapped_column(Boolean, default=True)
    metrics: Mapped[dict] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("name", "version", name="uq_model_version"),)


class TrainingRun(Base):
    __tablename__ = "training_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(60), index=True)
    model_version_id: Mapped[int | None] = mapped_column(ForeignKey("model_versions.id"))
    status: Mapped[str] = mapped_column(String(12), default="completed")
    data_version: Mapped[str] = mapped_column(String(60))
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doc_key: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(String(200))
    source_type: Mapped[str] = mapped_column(String(30))  # project_authored | official | other
    verified_official: Mapped[bool] = mapped_column(Boolean, default=False)
    published_date: Mapped[str | None] = mapped_column(String(10))
    language: Mapped[str] = mapped_column(String(12), default="en")
    content_hash: Mapped[str] = mapped_column(String(64))
    doc_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary)
    embedding_model: Mapped[str | None] = mapped_column(String(120))
    chunk_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    document: Mapped[KnowledgeDocument] = relationship(back_populates="chunks")
    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_doc_chunk"),)
