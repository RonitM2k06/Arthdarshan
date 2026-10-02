"""Evaluate the PRODUCTION detection path (rules + gated ML) on the hand-written held-out set.

This is the number that matters for users: it is exactly what runs inside /api/decisions (minus the choice-based signal).
Run automatically by ml.training.train; results are merged into ml/evaluation/misconception_clf_metrics.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

from ai.misconception import ml_models
from ai.misconception.detector import detect, detect_rules
from ai.misconception.taxonomy import MISCONCEPTION_IDS as LABELS

ROOT = Path(__file__).resolve().parents[2]


def evaluate() -> dict:
    ml_models.reset()
    held = json.loads((ROOT / "ml" / "datasets" / "heldout_misconception.json").read_text(encoding="utf-8"))["items"]
    Y = np.array([[int(lab in r["labels"]) for lab in LABELS] for r in held])

    def matrix(fn) -> np.ndarray:
        return np.array([[int(lab in fn(r["text"])) for lab in LABELS] for r in held])

    rules = matrix(lambda t: {d.id for d in detect_rules(t)})
    prod = matrix(lambda t: {d.id for d in detect(t, [], ml_models.predict_misconceptions(t), ml_models.misconception_threshold())})
    out = {}
    for name, P in (("rules_only", rules), ("production_rules_plus_gated_ml", prod)):
        p, r, f, _ = precision_recall_fscore_support(Y, P, average="micro", zero_division=0)
        mp, mr, mf, _ = precision_recall_fscore_support(Y, P, average="macro", zero_division=0)
        out[name] = {"micro": {"precision": round(float(p), 3), "recall": round(float(r), 3), "f1": round(float(f), 3)},
                     "macro": {"precision": round(float(mp), 3), "recall": round(float(mr), 3), "f1": round(float(mf), 3)}}
    # single-label confusion for the production path
    t_idx = [int(np.argmax(y)) if y.sum() else len(LABELS) for y in Y]
    p_idx = []
    for row in prod:
        p_idx.append(int(np.argmax(row)) if row.sum() else len(LABELS))
    cm = confusion_matrix(t_idx, p_idx, labels=list(range(len(LABELS) + 1)))
    out["production_confusion"] = {"labels": LABELS + ["none"], "matrix": cm.tolist(),
                                   "note": "rows true (first label or none), columns predicted (first detected label or none)"}
    out["n"] = len(held)
    out["caveat"] = "hand-written, n=80; indicative not definitive"
    return out


def main() -> dict:
    res = evaluate()
    path = ROOT / "ml" / "evaluation" / "misconception_clf_metrics.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["production_path_heldout"] = res
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    art = ROOT / "artifacts" / "ml_metrics.json"
    if art.exists():
        a = json.loads(art.read_text(encoding="utf-8"))
        a["results"]["misconception_clf"]["production_path_heldout"] = res
        art.write_text(json.dumps(a, indent=1, ensure_ascii=False), encoding="utf-8")
    return res


if __name__ == "__main__":
    print(json.dumps(main()["production_rules_plus_gated_ml"], indent=1))
