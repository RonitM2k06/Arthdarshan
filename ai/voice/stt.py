"""Local speech-to-text via faster-whisper (lazy, CPU int8). Falls back cleanly when unavailable."""
from __future__ import annotations

import logging
import tempfile
import threading
from pathlib import Path

from apps.api.config import get_settings

log = logging.getLogger("arth.stt")
_lock = threading.Lock()
_model = {"obj": None, "error": None}
LANG_HINT = {"en": "en", "hi": "hi", "hinglish": None}  # Hinglish: let Whisper auto-detect


def status() -> dict:
    s = get_settings()
    if s.low_resource:
        return {"available": False, "engine": "faster-whisper", "reason": "low-resource mode", "fallback": "browser_speech_or_text"}
    try:
        import faster_whisper  # noqa: F401
    except Exception:  # noqa: BLE001
        return {"available": False, "engine": "faster-whisper", "reason": "faster-whisper not installed", "fallback": "browser_speech_or_text"}
    return {"available": True, "engine": "faster-whisper", "model": s.whisper_model, "loaded": _model["obj"] is not None,
            "note": "model loads on first use (downloads once if not cached)", "fallback": "browser_speech_or_text"}


def _get():
    with _lock:
        if _model["obj"] is None:
            from faster_whisper import WhisperModel
            _model["obj"] = WhisperModel(get_settings().whisper_model, device="cpu", compute_type="int8")
        return _model["obj"]


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
        segs, info = _get().transcribe(path, language=LANG_HINT.get(language), vad_filter=True, beam_size=1)
        text = " ".join(s.text.strip() for s in segs).strip()
        return {"text": text, "language": info.language, "engine": "faster-whisper"}
    except Exception as exc:  # noqa: BLE001
        log.warning("transcription failed: %s", type(exc).__name__)
        raise RuntimeError("transcription failed") from exc
    finally:
        Path(path).unlink(missing_ok=True)
