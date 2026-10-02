"""Logging setup. Free-text learner reasoning is NEVER logged."""
from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from apps.api.config import ROOT, get_settings


def setup_logging() -> None:
    level = getattr(logging, get_settings().log_level.upper(), logging.INFO)
    root = logging.getLogger()
    if getattr(root, "_arth_configured", False):
        return
    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root.addHandler(sh)
    try:
        logs = Path(ROOT) / "artifacts" / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(logs / "api.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8")
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except OSError:
        pass
    root.setLevel(level)
    for noisy in ("httpx", "httpcore", "urllib3", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    root._arth_configured = True  # type: ignore[attr-defined]
