"""Generate SYNTHETIC datasets (deterministic, seeded). Output -> data/synthetic/*.jsonl with a version hash.

SYNTHETIC: these are template-composed learner statements and simulated learner histories. They exist only to bootstrap
lightweight local models before real usage data exists. Metrics computed on a random split of this data are optimistic;
the hand-written held-out set is the more honest check. Refit on real (consented, local) logs when available.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import numpy as np

from .phrases import (BEHAVIOUR_NONE, BEHAVIOUR_PHRASES, CLOSERS, CONTEXTS, MISC_CLAIMS, NONE_STATEMENTS, OPENERS)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "synthetic"
GENERATOR_VERSION = "synthetic-v1"


def _compose(rng: random.Random, core: str) -> str:
    t = rng.choice(CONTEXTS) + rng.choice(OPENERS) + core + rng.choice(CLOSERS)
    if rng.random() < 0.15:
        t = t.upper() if rng.random() < 0.3 else t.lower()
    if rng.random() < 0.12:  # light typo noise
        i = rng.randrange(len(t))
        t = t[:i] + t[i + 1:]
    return " ".join(t.split())


def misconception_dataset(seed: int = 13, per_class: int = 90, per_none: int = 220) -> list[dict]:
    rng = random.Random(seed)
    rows: list[dict] = []
    for mid, claims in MISC_CLAIMS.items():
        for _ in range(per_class):
            rows.append({"text": _compose(rng, rng.choice(claims)), "labels": [mid], "synthetic": True})
    # a few multi-label rows (two beliefs joined)
    ids = list(MISC_CLAIMS)
    for _ in range(120):
        a, b = rng.sample(ids, 2)
        rows.append({"text": _compose(rng, rng.choice(MISC_CLAIMS[a]) + " and " + rng.choice(MISC_CLAIMS[b])), "labels": sorted([a, b]), "synthetic": True})
    for _ in range(per_none):
        rows.append({"text": _compose(rng, rng.choice(NONE_STATEMENTS)), "labels": [], "synthetic": True})
    rng.shuffle(rows)
    return rows


def behaviour_dataset(seed: int = 21, per_class: int = 80, per_none: int = 160) -> list[dict]:
    rng = random.Random(seed)
    rows: list[dict] = []
    for lab, phrases in BEHAVIOUR_PHRASES.items():
        for _ in range(per_class):
            rows.append({"text": _compose(rng, rng.choice(phrases)), "labels": [lab], "synthetic": True})
    labs = list(BEHAVIOUR_PHRASES)
    for _ in range(150):
        a, b = rng.sample(labs, 2)
        rows.append({"text": _compose(rng, rng.choice(BEHAVIOUR_PHRASES[a]) + " and " + rng.choice(BEHAVIOUR_PHRASES[b])), "labels": sorted([a, b]), "synthetic": True})
    for _ in range(per_none):
        rows.append({"text": _compose(rng, rng.choice(BEHAVIOUR_NONE)), "labels": [], "synthetic": True})
    rng.shuffle(rows)
    return rows


def success_dataset(seed: int = 5, n_learners: int = 600, attempts: int = 8) -> list[dict]:
    """Simulated learner histories. Ground truth is a stated generative assumption (NOT observed human data):
    P(success) = sigmoid(4*(skill + 0.35*recent - 0.45) - 0.9*(difficulty - 1.5)); skill grows slowly with practice."""
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n_learners):
        skill = float(rng.beta(2, 3))
        recent, played, avg_dim = 0.0, 0, float(np.clip(skill + rng.normal(0, 0.08), 0, 1))
        hist: list[int] = []
        for _a in range(attempts):
            diff = int(rng.integers(1, 4))
            ready = float(np.clip(0.6 * skill + 0.4 * avg_dim + rng.normal(0, 0.04), 0, 1))
            recent = float(np.mean(hist[-5:])) if hist else 0.0
            logit = 4 * (skill + 0.35 * recent - 0.45) - 0.9 * (diff - 1.5)
            p = 1 / (1 + np.exp(-logit))
            y = int(rng.random() < p)
            rows.append({"features": [round(ready, 4), diff, round(recent, 4), round(avg_dim, 4), min(played, 10) / 10], "success": y, "synthetic": True})
            hist.append(y)
            played += 1
            skill = min(1.0, skill + 0.03 + 0.02 * y)
            avg_dim = float(np.clip(avg_dim + 0.02 * (2 * y - 1), 0, 1))
    return rows


def write_jsonl(rows: list[dict], name: str) -> tuple[Path, str]:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.jsonl"
    blob = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
    path.write_text(blob + "\n", encoding="utf-8")
    h = hashlib.sha256(blob.encode()).hexdigest()[:10]
    (OUT / f"{name}.meta.json").write_text(json.dumps({"name": name, "generator": GENERATOR_VERSION, "rows": len(rows), "sha256_10": h, "synthetic": True,
                                                       "warning": "SYNTHETIC data. Not real learner data."}, indent=1), encoding="utf-8")
    return path, f"{GENERATOR_VERSION}-{h}"


def build_all() -> dict[str, str]:
    versions = {}
    for name, fn in (("misconception", misconception_dataset), ("behaviour", behaviour_dataset), ("success", success_dataset)):
        _, v = write_jsonl(fn(), name)
        versions[name] = v
    return versions


if __name__ == "__main__":
    print(build_all())
