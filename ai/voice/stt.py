"""Local speech-to-text via faster-whisper, run in the isolated voice worker. Falls back cleanly when unavailable."""
from __future__ import annotations

import importlib.util
import logging
import tempfile
from pathlib import Path

from apps.api.config import get_settings
from . import rpc

log = logging.getLogger("arth.stt")
LANG_HINT = {"en": "en", "hi": "hi", "hinglish": None}  # Hinglish: let Whisper auto-detect


def status() -> dict:
    s = get_settings()
    if s.low_resource:
        return {"available": False, "engine": "faster-whisper", "reason": "low-resource mode", "fallback": "browser_speech_or_text"}
    if importlib.util.find_spec("faster_whisper") is None:
        return {"available": False, "engine": "faster-whisper", "reason": "faster-whisper not installed", "fallback": "browser_speech_or_text"}
    return {"available": True, "engine": "faster-whisper (isolated worker)", "model": s.whisper_model,
            "note": "model loads on first use (downloads once if not cached)", "fallback": "browser_speech_or_text"}


def transcribe(audio_bytes: bytes, language: str = "en", suffix: str = ".webm") -> dict:
    """Returns {text, language, engine}. Raises RuntimeError if STT is unavailable (caller falls back to text)."""
    st = status()
    if not st["available"]:
        raise RuntimeError(st["reason"])
    if not audio_bytes or len(audio_bytes) < 200:
        raise ValueError("audio is empty")
    if len(audio_bytes) > 15_000_000:
        raise ValueError("audio is too large")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_bytes)
        path = f.name
    try:
        head, _ = rpc.call({"op": "stt", "path": path, "language": LANG_HINT.get(language), "model": get_settings().whisper_model,
                          "model_dir": str(Path(get_settings().piper_voices_dir).parent / "models")}, timeout=600)
    except rpc.VoiceUnavailable as exc:
        raise RuntimeError(str(exc)) from exc
    finally:
        Path(path).unlink(missing_ok=True)
    if not head.get("ok"):
        log.warning("transcription failed: %s", head.get("error"))
        raise RuntimeError("transcription failed")
    return {"text": head["text"], "language": head.get("language"), "engine": "faster-whisper"}
