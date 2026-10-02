"""Optional local LLM via Ollama. Lazy, time-limited, and never required.

The LLM may *explain* and *interpret*; it never controls scenario truth, scoring or safety.
Every output goes through the Safety Gateway and a numeric-grounding check, with deterministic templates as fallback.
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
from typing import Any

import httpx

from apps.api.config import get_settings

log = logging.getLogger("arth.llm")
_lock = threading.Lock()
_cache: dict[str, Any] = {"t": 0.0, "status": None}
_STATUS_TTL = 10.0


def status(force: bool = False) -> dict:
    """Detect Ollama and the configured model. Cheap (cached) and never raises."""
    s = get_settings()
    if not s.llm_active:
        reason = "disabled by configuration" if not s.llm_enabled else "low-resource mode"
        return {"available": False, "model": s.llm_model, "reason": reason, "backend": "ollama"}
    now = time.time()
    with _lock:
        if not force and _cache["status"] is not None and now - _cache["t"] < _STATUS_TTL:
            return _cache["status"]
    result: dict[str, Any] = {"available": False, "model": s.llm_model, "backend": "ollama", "reason": ""}
    try:
        r = httpx.get(f"{s.ollama_url}/api/tags", timeout=1.5)
        r.raise_for_status()
        names = [m.get("name", "") for m in r.json().get("models", [])]
        base = s.llm_model.split(":")[0]
        have = any(n == s.llm_model or n.startswith(s.llm_model) or n.split(":")[0] == base and s.llm_model.endswith(n.split(":")[-1]) for n in names)
        if have:
            result.update(available=True, reason="ready", installed=names)
        else:
            result.update(reason=f"model '{s.llm_model}' not pulled (installed: {', '.join(names) or 'none'})", installed=names)
    except Exception as exc:  # noqa: BLE001
        result["reason"] = f"Ollama not reachable ({type(exc).__name__})"
    with _lock:
        _cache.update(t=now, status=result)
    return result


def generate(prompt: str, system: str, *, json_mode: bool = True, max_tokens: int = 220, temperature: float = 0.2,
             timeout: float | None = None) -> str | None:
    """Return model text or None on any failure/timeout. Loads the model lazily on first call; Ollama unloads it after keep_alive."""
    s = get_settings()
    if not status()["available"]:
        return None
    body = {"model": s.llm_model, "prompt": prompt, "system": system, "stream": False, "keep_alive": "3m",
            "options": {"temperature": temperature, "num_predict": max_tokens, "num_ctx": 2048}}
    if json_mode:
        body["format"] = "json"
    try:
        r = httpx.post(f"{s.ollama_url}/api/generate", json=body, timeout=timeout or s.llm_timeout)
        r.raise_for_status()
        return r.json().get("response", "").strip() or None
    except Exception as exc:  # noqa: BLE001
        log.warning("LLM call failed: %s", type(exc).__name__)
        with _lock:
            _cache["t"] = 0.0   # re-probe next time
        return None


def parse_json(text: str | None) -> dict | None:
    if not text:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                data = json.loads(m.group(0))
                return data if isinstance(data, dict) else None
            except json.JSONDecodeError:
                return None
    return None


_NUM = re.compile(r"(?:₹\s*)?\d[\d,]*(?:\.\d+)?\s*%?")


def numbers_grounded(output: str, facts_blob: str) -> bool:
    """Every number in the LLM text must already appear in the facts we supplied (no invented figures)."""
    allowed = {re.sub(r"[^\d.]", "", n) for n in _NUM.findall(facts_blob)}
    for n in _NUM.findall(output):
        key = re.sub(r"[^\d.]", "", n)
        if key and key not in allowed:
            return False
    return True


def reset_cache() -> None:
    with _lock:
        _cache.update(t=0.0, status=None)
