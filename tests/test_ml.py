import json
from pathlib import Path

import numpy as np
import pytest
from sklearn.metrics import precision_recall_fscore_support

from ai.misconception import ml_models
from ai.misconception.detector import detect
from ai.misconception.taxonomy import MISCONCEPTION_IDS
from ml.datasets import generate
from ml.evaluation import production_eval

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "ml" / "evaluation"


@pytest.fixture(autouse=True)
def _models():
    ml_models.reset()
    yield
    ml_models.reset()


def test_models_exist_and_are_marked_synthetic():
    for name in ("misconception_clf", "behaviour_clf", "success_model"):
        assert ml_models.available(name), f"run `python -m ml.training.train` ({name} missing)"
    import joblib
    for name in ("misconception_clf", "behaviour_clf", "success_model"):
        b = joblib.load(ROOT / "ml" / "models" / f"{name}.joblib")
        assert b["synthetic_data"] is True and b["data_version"].startswith("synthetic-") and b["trained_at"]


def test_metrics_files_report_real_artifacts_and_caveats():
    for name in ("misconception_clf", "behaviour_clf", "success_model"):
        m = json.loads((EVAL / f"{name}_metrics.json").read_text(encoding="utf-8"))
        assert m["synthetic_data"] is True and m["data_version"]
    mc = json.loads((EVAL / "misconception_clf_metrics.json").read_text(encoding="utf-8"))
    assert "caveat" in mc["synthetic_split"] and "caveat" in mc["heldout_handwritten"]
    assert len(mc["heldout_handwritten"]["confusion"]["matrix"]) == len(MISCONCEPTION_IDS) + 1
    for lab, v in mc["heldout_handwritten"]["per_label"].items():
        assert set(v) == {"precision", "recall", "f1", "support"}
    sm = json.loads((EVAL / "success_model_metrics.json").read_text(encoding="utf-8"))
    assert "SIMULATED" in sm["caveat"] and sm["confusion"]["matrix"]


def test_stored_heldout_metrics_match_a_fresh_evaluation():
    """No fabricated metrics: recompute from the saved model and compare with the stored JSON."""
    stored = json.loads((EVAL / "misconception_clf_metrics.json").read_text(encoding="utf-8"))
    held = json.loads((ROOT / "ml" / "datasets" / "heldout_misconception.json").read_text(encoding="utf-8"))["items"]
    thr = ml_models.misconception_threshold()
    Y = np.array([[int(l in r["labels"]) for l in MISCONCEPTION_IDS] for r in held])
    P = np.array([[int(ml_models.predict_misconceptions(r["text"]).get(l, 0) >= thr) for l in MISCONCEPTION_IDS] for r in held])
    p, r, f, _ = precision_recall_fscore_support(Y, P, average="micro", zero_division=0)
    assert round(float(f), 3) == stored["heldout_handwritten"]["micro"]["f1"]
    assert stored["heldout_handwritten"]["n"] == len(held)


def test_production_path_beats_rules_alone_on_heldout():
    res = production_eval.evaluate()
    assert res["production_rules_plus_gated_ml"]["micro"]["f1"] > res["rules_only"]["micro"]["f1"] + 0.2
    assert res["production_rules_plus_gated_ml"]["micro"]["precision"] >= 0.8       # false positives stay low
    assert res["production_rules_plus_gated_ml"]["micro"]["recall"] >= 0.6


def test_ml_generalises_beyond_rule_patterns():
    # paraphrases the regex rules do not cover
    from ai.misconception.detector import detect_rules
    for txt, mid in [("Costs are so small that I can ignore them", "M012"), ("Heavy technical vocabulary tells me it is credible", "M008"),
                     ("Paperwork can be dealt with after something happens", "M013")]:
        assert not detect_rules(txt)
        got = {d.id for d in detect(txt, [], ml_models.predict_misconceptions(txt), ml_models.misconception_threshold())}
        assert mid in got, (txt, got)


def test_ml_gating_skips_sceptical_and_tiny_text():
    skeptic = "Nobody can guarantee returns like that so it is a scam"
    probs = {"M001": 0.99}
    assert detect(skeptic, [], probs) == []
    assert detect("ok", [], probs) == []
    assert detect("it is guaranteed so safe", [], {"M001": 0.99})


def test_models_handle_empty_and_weird_input():
    assert ml_models.predict_misconceptions("") == {}
    assert ml_models.predict_misconceptions("   ") == {}
    assert isinstance(ml_models.predict_misconceptions("😀😀😀"), dict)
    assert isinstance(ml_models.predict_behaviours("x" * 5000), dict)


def test_success_model_monotone_in_difficulty():
    easy = ml_models.success_probability([0.5, 1, 0.5, 0.5, 0.3])
    hard = ml_models.success_probability([0.5, 3, 0.5, 0.5, 0.3])
    assert easy is not None and hard is not None and easy > hard
    assert ml_models.success_probability([0.9, 2, 0.9, 0.9, 1.0]) > ml_models.success_probability([0.1, 2, 0.0, 0.1, 0.0])


def test_dataset_generation_is_deterministic_and_labelled():
    a = generate.misconception_dataset()
    b = generate.misconception_dataset()
    assert a == b and all(r["synthetic"] is True for r in a)
    assert generate.success_dataset()[0]["synthetic"] is True
    meta = json.loads((ROOT / "data" / "synthetic" / "misconception.meta.json").read_text(encoding="utf-8"))
    assert meta["synthetic"] is True and "SYNTHETIC" in meta["warning"]
