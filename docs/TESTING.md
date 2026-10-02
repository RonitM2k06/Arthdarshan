# TESTING.md — last full run

| Suite | Command | Result |
|---|---|---|
| Backend (pytest) | `python -m pytest` | **292 passed** |
| Frontend unit (Vitest) | `cd apps/web && npm test` | **20 passed** |
| End-to-end + accessibility (Playwright, Edge) | `cd apps/web && npx playwright test` | **33 passed** |
| ML evaluation | `python -m ml.training.train` | precision / recall / F1 / confusion matrices written to `ml/evaluation/` (see ML.md) |

## What the backend suite covers

* **Scenario engine** — schema + validator (positive and negative cases), every transition of all 8 scenarios, determinism, evidence recall, answer-key secrecy, localisation, pressure types.
* **Safety** — 38 adversarial prompts, 19 benign prompts (false positives), 9 sensitive-data formats, 11 bad outputs, 6 good outputs, citation rule for regulatory claims, empty/oversized/emoji input.
* **Misconceptions** — positive and negative rule cases for M001–M013 (English + Hinglish), sceptical-sentence suppression, choice-signal merge, behaviour and emotion rules, non-judgemental wording.
* **ML** — models exist and are labelled synthetic; stored metrics equal a fresh recomputation; production path vs rules; gating; deterministic datasets; weird input.
* **Adaptive learning** — BKT bounds/monotonicity; new learner gets the hero; FOMO weakness → pressure scenarios; fee/diversification misconceptions → the matching scenarios and simulations; terminology → document scenario + lessons; resolved misconceptions ignored; repetition penalty; every recommendation explained.
* **Simulations** — 9 simulations: defaults, extremes, validation errors (NaN, strings, unknown params), numerical agreement with the concept text (₹4,66,096), monotonicity, seeded determinism, no advice language.
* **API** — auth, validation (422/400/404/409), full hero journey with improvement, misconception resolution over time, PII redaction in the DB, every scenario via first-safe path and random walks, concurrent sessions (threads), export/reset/delete, simulations, quiz, concept graph, RAG grounded answers and refusal, blocked advice via API, Evidence Lab, voice endpoints with fallbacks, models endpoint, **database failure → safe 503**, scripted persona through the real engine.
* **LLM** — deterministic explanation unaffected by the model; bad/advice/invented-number/ungrounded/timeout/garbage outputs dropped; English-only; low-resource and Ollama-unreachable status.
* **Voice** — real Piper WAV for 3 languages, TTS→STT round trip, works after scikit-learn is loaded, garbage audio does not kill the worker.
* **DB** — Alembic upgrade creates all 19 required tables (+ extras), downgrade to base works, no PII columns.

## What the browser suite covers

Landing (no external requests), the hero journey (impulsive then careful, misconception cards, fingerprint with "not measured" honesty, improvement ▲), all eight scenarios playable, Simple Mode (large text, confirmation dialog, no timer), Hindi/Hinglish rendering, concepts, live simulation sliders, Hinglish Q&A with sources, safety demo, Evidence Lab, mobile layout (no horizontal overflow on 7 pages), API-down message, export/delete, scripted persona, keyboard-only decision, skip link and `lang`, and **axe-core WCAG 2.x A/AA checks (zero serious/critical)** on 18 pages plus the player, feedback, summary and Simple Mode states.

## Not covered
Physical-device testing, Firefox/WebKit, screen-reader walkthroughs by a human, load testing, a usability study with real learners. See LIMITATIONS.md.
