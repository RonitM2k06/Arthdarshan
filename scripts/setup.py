"""First-time setup: python deps, database migrations + content sync, ML models, web deps + build.

    python scripts/setup.py              # core only (no big downloads)
    python scripts/setup.py --voice      # also install local STT/TTS libraries and download small Piper voices (~130 MB)
    python scripts/setup.py --llm        # also pull the small local LLM through Ollama (~2 GB; Ollama must be installed)
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"


def run(cmd: list[str], cwd: Path = ROOT, **kw) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True, **kw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", action="store_true")
    ap.add_argument("--llm", action="store_true")
    ap.add_argument("--skip-web", action="store_true")
    a = ap.parse_args()
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    run([sys.executable, "scripts/build_knowledge.py"], env=env)
    run([sys.executable, "scripts/build_scenarios.py"], env=env)
    run([sys.executable, "scripts/migrate.py"], env=env)
    if not (ROOT / "ml" / "models" / "misconception_clf.joblib").exists():
        run([sys.executable, "-m", "ml.training.train"], env=env)
    if a.voice:
        run([sys.executable, "-m", "pip", "install", "faster-whisper", "piper-tts", "av>=14,<17"])
        run([sys.executable, "-m", "piper.download_voices", "--download-dir", "data/voices", "en_US-lessac-low", "hi_IN-pratham-medium"])
    if a.llm:
        exe = shutil.which("ollama") or str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe")
        if Path(exe).exists():
            run([exe, "pull", "qwen2.5:3b-instruct"])
        else:
            print("Ollama is not installed (https://ollama.com). The app works without it.")
    if not a.skip_web:
        npm = shutil.which("npm.cmd") or shutil.which("npm")
        if not npm:
            print("Node.js not found: install Node 18+ to run the web UI.")
            return 1
        run([npm, "install", "--no-audit", "--no-fund"], cwd=WEB)
        run([npm, "run", "build"], cwd=WEB)
    print("\nSetup complete. Start with:  python scripts/demo.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
