"""Compile configs/scenario_src/*.py (authoring format) into configs/scenarios/*.json and validate them.

Usage: python scripts/build_scenarios.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "configs" / "scenario_src"
OUT = ROOT / "configs" / "scenarios"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SRC))


def main() -> int:
    from _lib import compile_scenario
    from ai.misconception.taxonomy import MISCONCEPTION_IDS
    from ai.scenario_engine.engine import load_scenario, validate_scenario
    from apps.api.services.content import concept_ids

    OUT.mkdir(parents=True, exist_ok=True)
    bad = 0
    for p in sorted(SRC.glob("s[0-9][0-9]_*.py")):
        spec = importlib.util.spec_from_file_location(p.stem, p)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        data = compile_scenario(mod.SC)
        sc = load_scenario(data)
        errs = validate_scenario(sc, known_concepts=concept_ids(), known_misconceptions=set(MISCONCEPTION_IDS))
        if errs:
            bad += 1
            print(f"[FAIL] {p.name}")
            for e in errs:
                print("   -", e)
            continue
        (OUT / f"{sc.id}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[ok] {sc.id}: {len(sc.states)} states, langs={list(sc.i18n)}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
