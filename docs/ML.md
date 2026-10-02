# ML.md — the locally trained models

Everything here is lightweight scikit-learn that trains in about 3 seconds on CPU: `python -m ml.training.train`. The point is *project-specific* ML where it adds something over rules, not a foundation model.

## What is trained

| Model | Task | Pipeline |
|---|---|---|
| `misconception_clf` | multi-label detection of M001–M013 from a learner's reasoning text | TF-IDF (word 1–2 grams + char 3–5 grams) → one-vs-rest logistic regression, threshold tuned on a validation split |
| `behaviour_clf` | multi-label behavioural pattern (social-proof reliance, urgency reaction, evidence-seeking, …, 12 labels) | same pipeline |
| `success_model` | P(learner succeeds on a scenario of a given difficulty) → used to pick scenarios in the "zone of proximal development" (target ≈ 0.65) | StandardScaler → logistic regression over `[readiness, difficulty, recent success rate, avg dimension score, sessions played]` |

Mastery *estimation* is **Bayesian Knowledge Tracing** (`ai/adaptive_learning/mastery.py`): a transparent probabilistic model with documented fixed parameters (p_init 0.20, learn 0.15, slip 0.10, guess 0.20). It is **not** fitted to data. The scenario-difficulty signal is the scenario's declared difficulty plus the success model's prediction.

## Data — all SYNTHETIC, labelled as such

* `ml/datasets/phrases.py` — learner statements written by the team (English + Hinglish), composed with random openers/closers/typo noise → `data/synthetic/*.jsonl` + `*.meta.json` (`"synthetic": true`, generator version, content hash). Same seed → byte-identical data (tested).
* The success model's labels come from a **simulated** generative process (documented in `ml/datasets/generate.py`). It encodes our assumptions about how difficulty and readiness interact; it is a calibrated *prior* for difficulty matching, **not** evidence about real learners.
* Two **hand-written held-out sets** (`ml/datasets/heldout_misconception.json`, n = 80; `heldout_behaviour.json`, n = 42) were written differently from the templates and before the models were evaluated. They are the more honest check — but they are small, so treat results as indicative.

## Results (copied from `ml/evaluation/*_metrics.json`, produced by the training script)

### Misconception classifier (13 labels, micro-averaged)

| Evaluation | Precision | Recall | F1 |
|---|---|---|---|
| Random 20 % split of synthetic data (n = 302) | 1.000 | 1.000 | 1.000 — **optimistic**: same templates as training |
| Hand-written held-out, ML alone (n = 80) | 0.679 | 0.877 | 0.765 |
| Hand-written held-out, regex rules alone | 1.000 | 0.246 | 0.395 |
| Hand-written held-out, rules OR ML (ungated) | 0.682 | 0.892 | 0.773 |
| **Hand-written held-out, production path (rules + gated ML)** | **0.902** | **0.708** | **0.793** |

Reading: rules are precise but miss most paraphrases; ML recovers recall but has false positives. The production path gates ML-only hits (needs probability ≥ max(threshold, 0.55), at least 3 words, and no sceptical phrasing like "scam", "can't be guaranteed") which trades some recall for much better precision. Per-label metrics and confusion matrices (synthetic split, held-out, production) are in the JSON files; per-label support on the held-out set is only 5, so per-label numbers are noisy.

### Behaviour classifier (12 labels)

| Evaluation | Precision | Recall | F1 |
|---|---|---|---|
| Synthetic split | 1.000 | 1.000 | 1.000 (optimistic) |
| Hand-written held-out, ML (n = 42) | 0.652 | 0.833 | 0.732 |
| Hand-written held-out, rules | 0.800 | 0.444 | 0.571 |
| rules OR ML | 0.612 | 0.833 | 0.706 |

Note rules-OR-ML is *lower* F1 than ML alone: the rules add false positives for some labels. We report it rather than hide it. In the product, behaviours are shown as "patterns noticed" with the evidence source, and the learner-facing text is explanatory, not a verdict.

### Success model (simulated labels)

AUC 0.821, F1 0.784, accuracy 0.745 versus a majority-class baseline of 0.589 (n_test = 960); Brier 0.170; confusion matrix `[[271,124],[121,444]]`. Coefficients: readiness +0.83, difficulty −0.70, recent success +0.53, sessions +0.14, avg dimension score +0.06. Because the labels are simulated, these numbers show the model recovers the *assumed* relationship; they say nothing about real learners until it is refit on consented local logs.

## Versioning

Each training run writes `model_versions` (name, version timestamp, data version hash, `synthetic_data=true`, full metrics) and `training_runs` rows, and the `.joblib` bundles carry `trained_at`, `data_version` and `synthetic_data`. `/api/models` exposes them; Settings shows whether the classifiers are active.

## Where the models are used (and how a failure degrades)

`apps/api/services/sessions.py` calls the detectors on each decision. If a model file is missing or fails to load, `ml_models` returns nothing and the rule layer plus the choice-based signals carry on. `recommend_next` uses the success model if present, otherwise a heuristic `readiness + 0.25 − 0.2·difficulty`.

## Tests

`tests/test_ml.py` asserts models exist and are marked synthetic, metric files contain caveats, **stored held-out F1 equals a fresh recomputation from the saved model** (no fabricated numbers), the production path beats rules alone by > 0.2 F1 with precision ≥ 0.8, gating skips sceptical/short text, weird inputs don't crash, and dataset generation is deterministic.
