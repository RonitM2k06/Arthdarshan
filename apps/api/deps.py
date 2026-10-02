"""Auth dependency. A learner is an anonymous local profile identified by a random bearer token."""
from __future__ import annotations

import hashlib
import secrets

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.errors import AppError
from database import models as m
from database.session import get_db


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_token() -> str:
    return secrets.token_urlsafe(32)


def current_user(authorization: str | None = Header(default=None), x_arth_token: str | None = Header(default=None),
                 db: Session = Depends(get_db)) -> m.User:
    token = x_arth_token
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token:
        raise AppError(401, "not_authenticated", "Start a learner profile first.")
    user = db.scalar(select(m.User).where(m.User.token_hash == hash_token(token)))
    if user is None:
        raise AppError(401, "invalid_token", "This profile was not found. Start a new one.")
    return user


def language(user: m.User = Depends(current_user), accept_language: str | None = Header(default=None, alias="X-Arth-Lang")) -> str:
    if accept_language in ("en", "hinglish", "hi"):
        return accept_language
    return user.language
