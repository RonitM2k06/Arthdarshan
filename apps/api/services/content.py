"""Loaders for static content (concepts, scenarios). Cached; content is read-only at runtime."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ai.scenario_engine.engine import load_scenarios_from_dir
from ai.scenario_engine.schema import Scenario
from apps.api.config import ROOT, get_settings


@lru_cache
def load_concepts() -> list[dict]:
    path = Path(get_settings().knowledge_dir) / "concepts.json"
    if not path.exists():  # first build (build_scenarios imports this before concepts.json exists)
        import subprocess
        import sys
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_knowledge.py")], check=True)
    return json.loads(path.read_text(encoding="utf-8"))


def concept_ids() -> set[str]:
    return {c["id"] for c in load_concepts()}


@lru_cache
def load_scenarios() -> dict[str, Scenario]:
    return {s.id: s for s in load_scenarios_from_dir(get_settings().scenarios_dir)}


def clear_content_cache() -> None:
    load_concepts.cache_clear()
    load_scenarios.cache_clear()
