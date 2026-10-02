"""Scenario schema (Pydantic). A scenario is DATA; the engine in engine.py is a pure function over it.

Structure: metadata, concept tags, difficulty, states (with pressure, evidence, actions),
transitions (action.next), consequences, scoring, reflection, optional i18n overlays.
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DIMENSIONS = [
    "concept_knowledge", "risk_recognition", "evidence_verification", "scam_awareness", "fomo_resistance",
    "herd_resistance", "emotional_discipline", "independent_reasoning", "uncertainty_awareness", "terminology",
]
PRESSURE_TYPES = ["urgency", "countdown", "scarcity", "social_proof", "authority", "fomo", "fear", "greed",
                  "loss_recovery", "peer_pressure", "emotional_story"]
Quality = Literal["safe", "mixed", "unsafe"]
EvidenceKind = Literal["red_flag", "neutral", "reassuring", "missing_info"]
CHANNELS = ["telegram", "whatsapp", "email", "document", "sms", "call", "app", "news", "chat", "none"]
MISCONCEPTION_RE = re.compile(r"^M\d{3}$")

DISCLAIMER = "SIMULATED · NO REAL MONEY · FICTIONAL SCENARIO"


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Character(_Base):
    name: str
    age: int = Field(ge=10, le=100)
    role: str


class Pressure(_Base):
    type: str
    text: str
    countdown_seconds: int | None = Field(default=None, gt=0, le=600)
    intensity: int = Field(default=2, ge=1, le=3)

    @field_validator("type")
    @classmethod
    def _type_ok(cls, v: str) -> str:
        if v not in PRESSURE_TYPES:
            raise ValueError(f"unknown pressure type {v!r}")
        return v


class Evidence(_Base):
    id: str
    label: str
    text: str
    kind: EvidenceKind
    why: str | None = None  # educational explanation shown after the decision (required for red flags)
    risk_factor: str | None = None  # short tag, e.g. "guaranteed_return"


class Observation(_Base):
    dimension: str
    value: float = Field(ge=0, le=100)

    @field_validator("dimension")
    @classmethod
    def _dim_ok(cls, v: str) -> str:
        if v not in DIMENSIONS:
            raise ValueError(f"unknown dimension {v!r}")
        return v


class Action(_Base):
    id: str
    label: str
    quality: Quality
    next: str
    consequence: str
    verification: bool | None = None  # True: user verifies independently; False: skips available verification
    requests_evidence: bool = False
    misconception_signals: list[str] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    concept_tags: list[str] = Field(default_factory=list)
    simple_label: str | None = None  # shorter wording for Simple Mode

    @field_validator("misconception_signals")
    @classmethod
    def _m_ok(cls, v: list[str]) -> list[str]:
        for m in v:
            if not MISCONCEPTION_RE.match(m):
                raise ValueError(f"bad misconception id {m!r}")
        return v


class Channel(_Base):
    type: str = "none"
    sender: str | None = None
    messages: list[str] = Field(default_factory=list)

    @field_validator("type")
    @classmethod
    def _t_ok(cls, v: str) -> str:
        if v not in CHANNELS:
            raise ValueError(f"unknown channel {v!r}")
        return v


class Outcome(_Base):
    kind: Quality
    headline: str
    summary: str
    simulated_loss: int | None = None  # fictional rupees, for display only


class State(_Base):
    id: str
    title: str
    narrative: str
    channel: Channel = Field(default_factory=Channel)
    pressure: list[Pressure] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)
    terminal: bool = False
    outcome: Outcome | None = None
    reasoning_prompt: str | None = None
    simulation_hint: str | None = None  # id of a consequence simulation relevant to this state


class MicroLesson(_Base):
    concept_id: str
    title: str
    body: str


class Reflection(_Base):
    key_points: list[str]
    questions: list[str] = Field(default_factory=list)
    micro_lesson: MicroLesson


class Scoring(_Base):
    dimensions: list[str]  # dimensions this scenario trains (focus)
    pass_quality: Quality = "safe"  # outcome quality counted as success for mastery

    @field_validator("dimensions")
    @classmethod
    def _d_ok(cls, v: list[str]) -> list[str]:
        for d in v:
            if d not in DIMENSIONS:
                raise ValueError(f"unknown dimension {d!r}")
        return v


class Scenario(_Base):
    id: str
    version: int = 1
    title: str
    tagline: str
    character: Character
    difficulty: int = Field(ge=1, le=3)
    concept_tags: list[str]
    pressure_tags: list[str]
    tests_misconceptions: list[str]
    initial_state: str
    states: dict[str, State]
    reflection: Reflection
    scoring: Scoring
    i18n: dict[str, dict[str, str]] = Field(default_factory=dict)
    disclaimer: str = DISCLAIMER
