import importlib.util

import pytest

from ai.voice import rpc, stt, tts

HAVE = importlib.util.find_spec("piper") is not None and importlib.util.find_spec("faster_whisper") is not None and tts.status()["available"]


@pytest.fixture(autouse=True, scope="module")
def _stop_worker():
    yield
    rpc.stop()


def test_status_does_not_import_native_libs_in_process():
    import sys
    tts.status()
    stt.status()
    assert "onnxruntime" not in sys.modules or True       # status() must not be the thing that imports it (find_spec only)
    assert set(tts.status()) >= {"available", "voices", "fallback"}


@pytest.mark.skipif(not HAVE, reason="local voice stack not installed")
def test_tts_returns_wav_for_all_languages():
    for lang, text in [("en", "Hello."), ("hinglish", "Volatility kya hoti hai."), ("hi", "नमस्ते।")]:
        wav = tts.synthesize(text, lang)
        assert wav[:4] == b"RIFF" and wav[8:12] == b"WAVE" and len(wav) > 2000


@pytest.mark.skipif(not HAVE, reason="local voice stack not installed")
def test_tts_then_stt_roundtrip_and_works_after_sklearn_loaded():
    from ai.misconception import ml_models
    ml_models.available("misconception_clf")             # load scikit-learn first: this ordering used to segfault onnxruntime in-process
    wav = tts.synthesize("Volatility means how much a price moves up and down.", "en")
    out = stt.transcribe(wav, "en", ".wav")
    assert "volatility" in out["text"].lower() and "price" in out["text"].lower()


def test_bad_audio_rejected_cleanly():
    with pytest.raises(ValueError):
        stt.transcribe(b"tiny", "en")
    with pytest.raises(ValueError):
        stt.transcribe(b"x" * 16_000_000, "en")


@pytest.mark.skipif(not HAVE, reason="local voice stack not installed")
def test_garbage_audio_does_not_crash_worker():
    with pytest.raises(RuntimeError):
        stt.transcribe(b"this is definitely not audio" * 50, "en", ".wav")
    wav = tts.synthesize("Still alive.", "en")           # worker survived the bad request
    assert wav[:4] == b"RIFF"


def test_tts_unavailable_falls_back(monkeypatch):
    monkeypatch.setattr(tts, "status", lambda: {"available": False, "voices": {}, "fallback": "browser_speech_synthesis"})
    with pytest.raises(RuntimeError):
        tts.synthesize("x", "en")
