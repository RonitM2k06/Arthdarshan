"""Voice worker process (child). Imports onnxruntime FIRST: on some Windows setups importing it after scikit-learn
segfaults, so Piper / faster-whisper live in this isolated process, never inside the API process.

Protocol (stdin/stdout, one JSON request per line):
  {"op":"tts","text":..., "voice":"<path>.onnx"}      -> {"ok":true,"len":N}\n + N bytes of WAV
  {"op":"stt","path":..., "language":"en|hi|None","model":"base"} -> {"ok":true,"text":...,"language":...}\n
  {"op":"ping"}                                        -> {"ok":true}\n
Errors -> {"ok":false,"error":"..."}\n  (the process stays alive).
"""
import io
import json
import sys
import wave

import onnxruntime  # noqa: F401  (must be imported before numpy/sklearn-style libraries)

_voices = {}
_whisper = {}


def _send(obj: dict, payload: bytes = b"") -> None:
    out = sys.stdout.buffer
    out.write((json.dumps(obj) + "\n").encode("utf-8"))
    if payload:
        out.write(payload)
    out.flush()


def do_tts(req: dict) -> None:
    from piper import PiperVoice
    path = req["voice"]
    if path not in _voices:
        _voices[path] = PiperVoice.load(path)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        _voices[path].synthesize_wav(req["text"], wf)
    data = buf.getvalue()
    _send({"ok": True, "len": len(data)}, data)


def _resolve_model(name: str, base_dir: str) -> str:
    """Download the CTranslate2 Whisper model into a plain folder (no symlinks: Windows without developer mode forbids them)."""
    import os
    if os.path.isdir(name):
        return name
    target = os.path.join(base_dir, f"whisper-{name}")
    if not os.path.exists(os.path.join(target, "model.bin")):
        from huggingface_hub import snapshot_download
        snapshot_download(f"Systran/faster-whisper-{name}", local_dir=target)
    return target


def do_stt(req: dict) -> None:
    from faster_whisper import WhisperModel
    name = req.get("model", "base")
    if name not in _whisper:
        _whisper[name] = WhisperModel(_resolve_model(name, req.get("model_dir", "data/models")), device="cpu", compute_type="int8")
    lang = req.get("language")
    segs, info = _whisper[name].transcribe(req["path"], language=None if lang in (None, "None", "") else lang, vad_filter=True, beam_size=1)
    _send({"ok": True, "text": " ".join(s.text.strip() for s in segs).strip(), "language": info.language})


def main() -> None:
    _send({"ok": True, "ready": True})
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            op = req.get("op")
            if op == "ping":
                _send({"ok": True})
            elif op == "tts":
                do_tts(req)
            elif op == "stt":
                do_stt(req)
            else:
                _send({"ok": False, "error": f"unknown op {op!r}"})
        except Exception as exc:  # noqa: BLE001
            _send({"ok": False, "error": f"{type(exc).__name__}: {exc}"[:300]})


if __name__ == "__main__":
    main()
