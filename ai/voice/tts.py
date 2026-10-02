"""Local text-to-speech via Piper (lazy). If no voice is installed the client falls back to browser speechSynthesis."""
from __future__ import annotations

import io
import logging
import re
import threading
import wave
from pathlib import Path

from apps.api.config import get_settings

log = logging.getLogger("arth.tts")
_lock = threading.Lock()
_voices: dict[str, object] = {}
# Hinglish is Hindi written in Roman letters; the English voice reads it intelligibly. Devanagari uses the Hindi voice.
VOICE_FOR = {"en": "en_US-lessac-low", "hinglish": "en_US-lessac-low", "hi": "hi_IN-pratham-medium"}


def _voice_path(name: str) -> Path:
    return Path(get_settings().piper_voices_dir) / f"{name}.onnx"


def status() -> dict:
    s = get_settings()
    try:
        import piper  # noqa: F401
        have_lib = True
    except Exception:  # noqa: BLE001
        have_lib = False
    voices = {lang: _voice_path(v).exists() for lang, v in VOICE_FOR.items()}
    return {"available": have_lib and any(voices.values()) and not s.low_resource, "engine": "piper", "library": have_lib, "voices": voices,
            "fallback": "browser_speech_synthesis"}


def clean_for_speech(text: str) -> str:
    text = re.sub(r"[“”\"*_`#]", "", text)
    text = text.replace("₹", "rupees ").replace("%", " percent").replace("→", ",").replace("·", ",")
    return re.sub(r"\s+", " ", text).strip()[:1500]


def synthesize(text: str, language: str = "en") -> bytes:
    """Return WAV bytes. Raises RuntimeError when TTS is unavailable (caller falls back to the browser)."""
    st = status()
    if not st["available"]:
        raise RuntimeError("local TTS unavailable")
    name = VOICE_FOR.get(language, VOICE_FOR["en"])
    if not _voice_path(name).exists():
        name = VOICE_FOR["en"]
        if not _voice_path(name).exists():
            raise RuntimeError("no Piper voice installed")
    with _lock:
        if name not in _voices:
            from piper import PiperVoice
            _voices[name] = PiperVoice.load(str(_voice_path(name)))
        voice = _voices[name]
    buf = io.BytesIO()
    try:
        with wave.open(buf, "wb") as wf:
            voice.synthesize_wav(clean_for_speech(text), wf)  # type: ignore[attr-defined]
    except Exception as exc:  # noqa: BLE001
        log.warning("synthesis failed: %s", type(exc).__name__)
        raise RuntimeError("synthesis failed") from exc
    return buf.getvalue()
