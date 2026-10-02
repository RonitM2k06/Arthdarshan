"""One-command launcher.

    python scripts/demo.py            # start API + web, open the hero journey (THE GUARANTEED OPPORTUNITY)
    python scripts/demo.py --dev      # use the Next.js dev server (hot reload) instead of the production build
    python scripts/demo.py --no-browser
    python scripts/demo.py --low-resource   # no LLM / no embeddings / no local STT (templates + keyword retrieval only)

Works offline after installation. The core simulator needs no internet, LLM, GPU or model download.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
API_PORT, WEB_PORT = 8000, 3000


def up(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 (localhost only)
            return r.status < 500
    except Exception:  # noqa: BLE001
        return False


def wait_for(url: str, seconds: int, label: str) -> bool:
    t0 = time.time()
    while time.time() - t0 < seconds:
        if up(url):
            return True
        time.sleep(0.6)
    print(f"[demo] {label} did not become ready within {seconds}s", file=sys.stderr)
    return False


def npm() -> str:
    exe = shutil.which("npm.cmd") or shutil.which("npm")
    if not exe:
        sys.exit("[demo] Node.js/npm not found. Install Node 18+ from https://nodejs.org")
    return exe


def ensure_ollama(env: dict) -> None:
    """Best effort: start Ollama if installed but not running (optional; the app works without it)."""
    if up("http://127.0.0.1:11434/api/tags", 1.0):
        return
    exe = shutil.which("ollama") or str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe")
    if exe and Path(exe).exists():
        try:
            subprocess.Popen([exe, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            time.sleep(2)
            print("[demo] started local Ollama")
        except OSError:
            pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--low-resource", action="store_true")
    ap.add_argument("--path", default="/demo", help="page to open (default /demo = fresh demo profile into the hero scenario)")
    args = ap.parse_args()

    env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONIOENCODING": "utf-8"}
    if args.low_resource:
        env["ARTH_LOW_RESOURCE"] = "1"
    procs: list[subprocess.Popen] = []

    try:
        # --- API ---------------------------------------------------------------------------
        if up(f"http://127.0.0.1:{API_PORT}/api/health"):
            print(f"[demo] API already running on :{API_PORT}")
        else:
            if not args.low_resource:
                ensure_ollama(env)
            print("[demo] starting API (migrations + content sync run automatically)…")
            procs.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "apps.api.main:app", "--host", "127.0.0.1", "--port", str(API_PORT), "--log-level", "warning"], cwd=ROOT, env=env))
            if not wait_for(f"http://127.0.0.1:{API_PORT}/api/health", 90, "API"):
                return 1
        # --- Web ---------------------------------------------------------------------------
        if up(f"http://127.0.0.1:{WEB_PORT}/"):
            print(f"[demo] web already running on :{WEB_PORT}")
        else:
            if not (WEB / "node_modules").exists():
                print("[demo] installing web dependencies (one time)…")
                subprocess.run([npm(), "install", "--no-audit", "--no-fund"], cwd=WEB, check=True)
            if args.dev:
                cmd = [npm(), "run", "dev"]
            else:
                if not (WEB / ".next" / "BUILD_ID").exists():
                    print("[demo] building the web app (one time, ~1 minute)…")
                    subprocess.run([npm(), "run", "build"], cwd=WEB, check=True, env=env)
                cmd = [npm(), "run", "start"]
            procs.append(subprocess.Popen(cmd, cwd=WEB, env=env, stdout=subprocess.DEVNULL))
            if not wait_for(f"http://127.0.0.1:{WEB_PORT}/", 120, "web app"):
                return 1
        url = f"http://localhost:{WEB_PORT}{args.path}"
        print(f"\n  ARTHDARSHAN is running.\n  Open: {url}\n  API docs: http://127.0.0.1:{API_PORT}/docs\n  Press Ctrl+C to stop.\n")
        if not args.no_browser:
            webbrowser.open(url)
        while procs and all(p.poll() is None for p in procs):
            time.sleep(1)
        return 0
    except KeyboardInterrupt:
        print("\n[demo] stopping…")
        return 0
    finally:
        for p in procs:
            if p.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
                else:
                    p.terminate()


if __name__ == "__main__":
    raise SystemExit(main())
