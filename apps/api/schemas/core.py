from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Lang = Literal["en", "hinglish", "hi"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AuthStart(Strict):
    display_name: str | None = Field(default=None, max_length=40)
    language: Lang = "en"
    simple_mode: bool = False


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    display_name: str | None
    language: str
    simple_mode: bool
    is_demo: bool
    streak_days: int
    created_at: datetime


class AuthOut(BaseModel):
    token: str
    user: UserOut


class UserUpdate(Strict):
    display_name: str | None = Field(default=None, max_length=40)
    language: Lang | None = None
    simple_mode: bool | None = None


class StartSession(Strict):
    scenario_id: str = Field(min_length=1, max_length=60)
    selection_id: int | None = None


class DecisionIn(Strict):
    session_id: str = Field(min_length=36, max_length=36)
    state_key: str = Field(min_length=1, max_length=60)
    action_id: str = Field(min_length=1, max_length=60)
    reasoning: str = Field(default="", max_length=1200)
    confidence: int | None = Field(default=None, ge=1, le=5)
    latency_ms: int | None = Field(default=None, ge=0, le=86_400_000)
    evidence_noticed: list[str] = Field(default_factory=list, max_length=40)
    countdown_expired: bool = False

    @field_validator("evidence_noticed")
    @classmethod
    def _ids(cls, v: list[str]) -> list[str]:
        return [x[:60] for x in v]


class QuizAnswerIn(Strict):
    question_id: str = Field(min_length=1, max_length=60)
    selected_index: int = Field(ge=0, le=9)
    latency_ms: int | None = Field(default=None, ge=0, le=3_600_000)


class SimRunIn(Strict):
    params: dict[str, float | int] = Field(default_factory=dict)


class AskIn(Strict):
    question: str = Field(min_length=1, max_length=500)
    language: Lang | None = None


class SafetyCheckIn(Strict):
    text: str = Field(max_length=4000)
    direction: Literal["input", "output"] = "input"


class VoiceTTSIn(Strict):
    text: str = Field(min_length=1, max_length=1500)
    language: Lang = "en"
