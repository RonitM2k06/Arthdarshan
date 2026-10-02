"""Local text-to-speech via Piper, run in an isolated worker process (see worker.py). If no voice is installed or the
worker fails, the client falls back to browser speechSynthesis."""
from __future__ import annotations

import importlib.util
import logging
import re
from pathlib import Path

from apps.api.config import get_settings
from . import rpc

log = logging.getLogger("arth.tts")
# Hinglish is Hindi written in Roman letters; the English voice reads it intelligibly. Devanagari uses the Hindi voice.
VOICE_FOR = {"en": "en_US-lessac-low", "hinglish": "en_US-lessac-low", "hi": "hi_IN-pratham-medium"}


def _voice_path(name: str) -> Path:
    return Path(get_settings().piper_voices_dir) / f"{name}.onnx"


def status() -> dict:
    s = get_settings()
    have_lib = importlib.util.find_spec("piper") is not None   # no native import inside the API process
    voices = {lang: _voice_path(v).exists() for lang, v in VOICE_FOR.items()}
    return {"available": have_lib and any(voices.values()) and not s.low_resource, "engine": "piper (isolated worker)", "library": have_lib,
            "voices": voices, "fallback": "browser_speech_synthesis"}


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
    try:
        head, payload = rpc.call({"op": "tts", "text": clean_for_speech(text), "voice": str(_voice_path(name))}, timeout=90)
    except rpc.VoiceUnavailable as exc:
        raise RuntimeError(str(exc)) from exc
    if not head.get("ok"):
        log.warning("synthesis failed: %s", head.get("error"))
        raise RuntimeError("synthesis failed")
    return payload
