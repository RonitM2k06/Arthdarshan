"""Lazy loader for the locally trained classifiers (see ml/training). Returns nothing if no model has been trained.

Models: misconception_clf (multi-label, M001-M013), behaviour_clf (multi-label), success_model (mastery/adaptive).
All are small scikit-learn pipelines; loading is lazy and cached.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

from apps.api.config import get_settings

log = logging.getLogger("arth.ml")
_lock = threading.Lock()
_cache: dict[str, Any] = {}


def _load(name: str) -> Any | None:
    with _lock:
        if name in _cache:
            return _cache[name]
        path = Path(get_settings().models_dir) / f"{name}.joblib"
        obj = None
        if path.exists():
            try:
                import joblib
                obj = joblib.load(path)
            except Exception as exc:  # noqa: BLE001
                log.warning("could not load model %s: %s", name, type(exc).__name__)
        _cache[name] = obj
        return obj


def reset() -> None:
    with _lock:
        _cache.clear()


def available(name: str) -> bool:
    return _load(name) is not None


def predict_misconceptions(text: str) -> dict[str, float]:
    bundle = _load("misconception_clf")
    if not bundle or not text or not text.strip():
        return {}
    try:
        arr = bundle["pipeline"].predict_proba([text])[0]
        return {lab: float(p) for lab, p in zip(bundle["labels"], arr)}
    except Exception as exc:  # noqa: BLE001
        log.warning("misconception model failed: %s", type(exc).__name__)
        return {}


def misconception_threshold() -> float:
    bundle = _load("misconception_clf")
    return float(bundle.get("threshold", 0.5)) if bundle else 0.5


def predict_behaviours(text: str) -> dict[str, float]:
    bundle = _load("behaviour_clf")
    if not bundle or not text or not text.strip():
        return {}
    try:
        arr = bundle["pipeline"].predict_proba([text])[0]
        return {lab: float(p) for lab, p in zip(bundle["labels"], arr)}
    except Exception as exc:  # noqa: BLE001
        log.warning("behaviour model failed: %s", type(exc).__name__)
        return {}


def behaviour_threshold() -> float:
    bundle = _load("behaviour_clf")
    return float(bundle.get("threshold", 0.5)) if bundle else 0.5


def success_probability(features: list[float]) -> float | None:
    bundle = _load("success_model")
    if not bundle:
        return None
    try:
        return float(bundle["pipeline"].predict_proba([features])[0][1])
    except Exception as exc:  # noqa: BLE001
        log.warning("success model failed: %s", type(exc).__name__)
        return None
