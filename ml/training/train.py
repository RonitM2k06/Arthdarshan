"""Train and evaluate the lightweight local models. Run:  python -m ml.training.train

Models (all scikit-learn, CPU, seconds to train):
  misconception_clf  TF-IDF(word+char) + one-vs-rest LogisticRegression  (multi-label M001..M013)
  behaviour_clf      same pipeline over 12 behaviour labels
  success_model      StandardScaler + LogisticRegression predicting P(success) for adaptive difficulty selection

Evaluation (computed here from real predictions, saved to ml/evaluation/ and artifacts/):
  precision / recall / F1 per label, micro & macro averages, confusion matrix, on
    (a) a random 20% split of the SYNTHETIC data (optimistic: same templates), and
    (b) a hand-written held-out set (more honest; small n).
  Rule-layer baseline vs ML vs combined is reported on (b).
No number in docs is typed by hand: it is copied from the JSON written by this script.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.compose import ColumnTransformer  # noqa: F401  (kept for future feature work)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, brier_score_loss, confusion_matrix, f1_score, precision_recall_fscore_support, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import FeatureUnion, Pipeline, make_pipeline
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ai.misconception import behaviour as bh  # noqa: E402
from ai.misconception.detector import detect_rules  # noqa: E402
from ai.misconception.taxonomy import MISCONCEPTION_IDS  # noqa: E402
from ml.datasets import generate  # noqa: E402

MODELS = ROOT / "ml" / "models"
EVAL = ROOT / "ml" / "evaluation"
ART = ROOT / "artifacts"
BEH_LABELS = list(bh.BEHAVIOURS)
SEED = 42


def text_pipeline() -> Pipeline:
    feats = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, lowercase=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True, lowercase=True)),
    ])
    clf = OneVsRestClassifier(LogisticRegression(C=6.0, max_iter=2000, class_weight="balanced", solver="liblinear"))
    return Pipeline([("features", feats), ("clf", clf)])


def per_label_report(y_true: np.ndarray, y_pred: np.ndarray, labels: list[str]) -> dict:
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, average=None, zero_division=0)
    per = {lab: {"precision": round(float(p[i]), 3), "recall": round(float(r[i]), 3), "f1": round(float(f[i]), 3), "support": int(s[i])} for i, lab in enumerate(labels)}
    mi = precision_recall_fscore_support(y_true, y_pred, average="micro", zero_division=0)
    ma = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    return {"per_label": per, "micro": {"precision": round(float(mi[0]), 3), "recall": round(float(mi[1]), 3), "f1": round(float(mi[2]), 3)},
            "macro": {"precision": round(float(ma[0]), 3), "recall": round(float(ma[1]), 3), "f1": round(float(ma[2]), 3)},
            "exact_match": round(float(accuracy_score(y_true, y_pred)), 3)}


def argmax_confusion(y_true: np.ndarray, probs: np.ndarray, labels: list[str], thr: float) -> dict:
    """Single-label view for a readable confusion matrix: true = first label (or 'none'); predicted = argmax if >= thr else 'none'."""
    names = labels + ["none"]
    t_idx, p_idx = [], []
    for i in range(len(y_true)):
        t_idx.append(int(np.argmax(y_true[i])) if y_true[i].sum() else len(labels))
        p_idx.append(int(np.argmax(probs[i])) if probs[i].max() >= thr else len(labels))
    cm = confusion_matrix(t_idx, p_idx, labels=list(range(len(names))))
    return {"labels": names, "matrix": cm.tolist(), "note": "rows = true (first label or none), columns = predicted (argmax if >= threshold else none)"}


def tune_threshold(y_val: np.ndarray, probs: np.ndarray) -> float:
    best, best_f = 0.5, -1.0
    for t in np.arange(0.2, 0.85, 0.05):
        f = f1_score(y_val, (probs >= t).astype(int), average="micro", zero_division=0)
        if f > best_f:
            best, best_f = float(round(t, 2)), f
    return best


def rules_matrix(texts: list[str], labels: list[str], kind: str = "misconception") -> np.ndarray:
    out = np.zeros((len(texts), len(labels)), dtype=int)
    for i, t in enumerate(texts):
        got = {d.id for d in detect_rules(t)} if kind == "misconception" else {h.label for h in bh.classify_rules(t)}
        for j, lab in enumerate(labels):
            out[i, j] = int(lab in got)
    return out


def train_text_model(name: str, rows: list[dict], labels: list[str], heldout: list[dict] | None, data_version: str) -> dict:
    texts = [r["text"] for r in rows]
    mlb = MultiLabelBinarizer(classes=labels)
    Y = mlb.fit_transform([r["labels"] for r in rows])
    X_tr, X_te, y_tr, y_te = train_test_split(texts, Y, test_size=0.2, random_state=SEED)
    X_fit, X_val, y_fit, y_val = train_test_split(X_tr, y_tr, test_size=0.15, random_state=SEED)
    pipe = text_pipeline()
    t0 = time.time()
    pipe.fit(X_fit, y_fit)
    thr = tune_threshold(y_val, pipe.predict_proba(X_val))
    pipe.fit(X_tr, y_tr)  # refit on train+val with the chosen threshold
    train_s = time.time() - t0
    probs_te = pipe.predict_proba(X_te)
    pred_te = (probs_te >= thr).astype(int)
    metrics: dict = {"model": name, "data_version": data_version, "synthetic_data": True, "threshold": thr, "n_train": len(X_tr), "n_test_synthetic": len(X_te),
                     "train_seconds": round(train_s, 2),
                     "synthetic_split": per_label_report(y_te, pred_te, labels) | {"confusion": argmax_confusion(y_te, probs_te, labels, thr),
                                                                               "caveat": "random split of template-generated data: optimistic, same phrasing as training"}}
    if heldout:
        h_texts = [r["text"] for r in heldout]
        h_Y = mlb.transform([r["labels"] for r in heldout])
        h_probs = pipe.predict_proba(h_texts)
        h_pred = (h_probs >= thr).astype(int)
        ml_report = per_label_report(h_Y, h_pred, labels)
        metrics["heldout_handwritten"] = ml_report | {"n": len(heldout), "confusion": argmax_confusion(h_Y, h_probs, labels, thr),
                                                      "caveat": "hand-written, differently worded, small n; indicative not definitive"}
        if True:
            r_pred = rules_matrix(h_texts, labels, "misconception" if name == "misconception_clf" else "behaviour")
            comb = np.maximum(r_pred, h_pred)
            metrics["heldout_rules_only"] = per_label_report(h_Y, r_pred, labels)
            metrics["heldout_combined_rules_or_ml"] = per_label_report(h_Y, comb, labels)
    bundle = {"pipeline": pipe, "labels": labels, "threshold": thr, "data_version": data_version, "trained_at": datetime.now(timezone.utc).isoformat(),
              "synthetic_data": True}
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODELS / f"{name}.joblib", compress=3)
    return metrics


def train_success_model(rows: list[dict], data_version: str) -> dict:
    X = np.array([r["features"] for r in rows], dtype=float)
    y = np.array([r["success"] for r in rows], dtype=int)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=y)
    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    pipe.fit(X_tr, y_tr)
    p = pipe.predict_proba(X_te)[:, 1]
    pred = (p >= 0.5).astype(int)
    pr = precision_recall_fscore_support(y_te, pred, average="binary", zero_division=0)
    base = max(y_te.mean(), 1 - y_te.mean())
    metrics = {"model": "success_model", "data_version": data_version, "synthetic_data": True, "n_train": int(len(X_tr)), "n_test": int(len(X_te)),
               "precision": round(float(pr[0]), 3), "recall": round(float(pr[1]), 3), "f1": round(float(pr[2]), 3), "roc_auc": round(float(roc_auc_score(y_te, p)), 3),
               "brier": round(float(brier_score_loss(y_te, p)), 3), "accuracy": round(float(accuracy_score(y_te, pred)), 3), "majority_baseline_accuracy": round(float(base), 3),
               "confusion": {"labels": ["fail", "success"], "matrix": confusion_matrix(y_te, pred).tolist()},
               "coefficients": dict(zip(["ready", "difficulty", "recent_success_rate", "avg_dimension_score", "n_sessions"], [round(float(c), 3) for c in pipe[-1].coef_[0]])),
               "caveat": "labels come from a SIMULATED generative process (assumptions in ml/datasets/generate.py), not observed learners; "
                         "this is a calibrated prior for difficulty matching and should be refit on real local logs"}
    joblib.dump({"pipeline": pipe, "features": ["ready", "difficulty", "recent_success_rate", "avg_dimension_score", "n_sessions"], "data_version": data_version,
                 "trained_at": datetime.now(timezone.utc).isoformat(), "synthetic_data": True}, MODELS / "success_model.joblib", compress=3)
    return metrics


def record_in_db(all_metrics: dict[str, dict]) -> None:
    """Register model versions and training runs in the database (best effort: training works without a DB)."""
    try:
        from apps.api.config import get_settings
        from database import models as m
        from database import session as dbs
        dbs.init_engine(get_settings().database_url)
        dbs.run_migrations(get_settings().database_url)
        with dbs.session_scope() as db:
            from sqlalchemy import select
            for name, met in all_metrics.items():
                version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                for old in db.scalars(select(m.ModelVersion).where(m.ModelVersion.name == name, m.ModelVersion.active.is_(True))):
                    old.active = False
                mv = m.ModelVersion(name=name, version=version, kind="sklearn", path=str((MODELS / f"{name}.joblib").relative_to(ROOT)).replace("\\", "/"),
                                    data_version=met["data_version"], synthetic_data=True, metrics=met, active=True)
                db.add(mv)
                db.flush()
                db.add(m.TrainingRun(model_name=name, model_version_id=mv.id, status="completed", data_version=met["data_version"],
                                     params={"seed": SEED}, metrics={k: v for k, v in met.items() if k in ("precision", "recall", "f1", "roc_auc", "threshold")} |
                                     ({"heldout_micro_f1": met["heldout_handwritten"]["micro"]["f1"]} if "heldout_handwritten" in met else {}),
                                     finished_at=datetime.now(timezone.utc)))
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] could not record in DB: {type(exc).__name__}: {exc}")


def main() -> int:
    versions = generate.build_all()
    load = lambda n: [json.loads(l) for l in (ROOT / "data" / "synthetic" / f"{n}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]  # noqa: E731
    held = json.loads((ROOT / "ml" / "datasets" / "heldout_misconception.json").read_text(encoding="utf-8"))["items"]
    held_b = json.loads((ROOT / "ml" / "datasets" / "heldout_behaviour.json").read_text(encoding="utf-8"))["items"]
    results = {
        "misconception_clf": train_text_model("misconception_clf", load("misconception"), MISCONCEPTION_IDS, held, versions["misconception"]),
        "behaviour_clf": train_text_model("behaviour_clf", load("behaviour"), BEH_LABELS, held_b, versions["behaviour"]),
        "success_model": train_success_model(load("success"), versions["success"]),
    }
    EVAL.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    for name, met in results.items():
        (EVAL / f"{name}_metrics.json").write_text(json.dumps(met, indent=1, ensure_ascii=False), encoding="utf-8")
    (ART / "ml_metrics.json").write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), "results": results}, indent=1, ensure_ascii=False), encoding="utf-8")
    from ml.evaluation import production_eval
    prod = production_eval.main()
    results["misconception_clf"]["production_path_heldout"] = prod
    record_in_db(results)
    mc = results["misconception_clf"]
    print("misconception_clf  synthetic-split micro-F1 =", mc["synthetic_split"]["micro"]["f1"], "| hand-written held-out micro-F1 =", mc["heldout_handwritten"]["micro"]["f1"],
          f"(n={mc['heldout_handwritten']['n']}) | rules-only =", mc["heldout_rules_only"]["micro"]["f1"], "| rules|ML =", mc["heldout_combined_rules_or_ml"]["micro"]["f1"])
    pp = prod["production_rules_plus_gated_ml"]["micro"]
    print("PRODUCTION path (rules + gated ML) on hand-written held-out: precision =", pp["precision"], "recall =", pp["recall"], "F1 =", pp["f1"])
    bc = results["behaviour_clf"]
    print("behaviour_clf      synthetic-split micro-F1 =", bc["synthetic_split"]["micro"]["f1"], "| hand-written held-out micro-F1 =", bc["heldout_handwritten"]["micro"]["f1"],
          f"(n={bc['heldout_handwritten']['n']}) | rules-only =", bc["heldout_rules_only"]["micro"]["f1"], "| rules|ML =", bc["heldout_combined_rules_or_ml"]["micro"]["f1"])
    sm = results["success_model"]
    print("success_model      AUC =", sm["roc_auc"], "F1 =", sm["f1"], "accuracy =", sm["accuracy"], "(majority baseline", sm["majority_baseline_accuracy"], ")")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
