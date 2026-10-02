"""Parent-side client for the isolated voice worker. Lazily started, restarted on failure, killed on timeout."""
from __future__ import annotations

import json
import logging
import subprocess
import sys
import threading
from pathlib import Path

from apps.api.config import ROOT

log = logging.getLogger("arth.voice.rpc")
_lock = threading.Lock()
_proc: subprocess.Popen | None = None


class VoiceUnavailable(RuntimeError):
    pass


def _start() -> subprocess.Popen:
    global _proc
    if _proc is not None and _proc.poll() is None:
        return _proc
    try:
        _proc = subprocess.Popen([sys.executable, "-m", "ai.voice.worker"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 cwd=str(ROOT), env={**__import__("os").environ, "PYTHONPATH": str(ROOT), "PYTHONIOENCODING": "utf-8"})
        ready = _proc.stdout.readline()  # type: ignore[union-attr]
        if not ready or not json.loads(ready).get("ready"):
            raise VoiceUnavailable("voice worker failed to start")
    except VoiceUnavailable:
        stop()
        raise
    except Exception as exc:  # noqa: BLE001
        stop()
        raise VoiceUnavailable(f"voice worker could not start ({type(exc).__name__})") from exc
    return _proc


def stop() -> None:
    global _proc
    if _proc is not None:
        try:
            _proc.kill()
        except Exception:  # noqa: BLE001
            pass
        _proc = None


def call(req: dict, timeout: float = 60.0) -> tuple[dict, bytes]:
    """Send one request. Returns (header, payload). Raises VoiceUnavailable on failure/timeout (worker is restarted next call)."""
    with _lock:
        proc = _start()
        timer = threading.Timer(timeout, stop)
        timer.start()
        try:
            proc.stdin.write((json.dumps(req) + "\n").encode("utf-8"))  # type: ignore[union-attr]
            proc.stdin.flush()  # type: ignore[union-attr]
            line = proc.stdout.readline()  # type: ignore[union-attr]
            if not line:
                raise VoiceUnavailable("voice worker stopped responding")
            head = json.loads(line)
            payload = b""
            if head.get("ok") and head.get("len"):
                payload = proc.stdout.read(head["len"])  # type: ignore[union-attr]
                if len(payload) != head["len"]:
                    raise VoiceUnavailable("voice worker returned incomplete audio")
            return head, payload
        except VoiceUnavailable:
            stop()
            raise
        except Exception as exc:  # noqa: BLE001
            stop()
            raise VoiceUnavailable(f"voice request failed ({type(exc).__name__})") from exc
        finally:
            timer.cancel()
