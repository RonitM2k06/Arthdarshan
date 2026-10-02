# LIMITATIONS.md — what is genuinely not done or not proven

Stated plainly so nobody has to discover them.

## Evidence and ML
* **No study of real learners.** Nothing here shows that the simulator improves real-world behaviour. The fingerprint measures behaviour *inside the simulation*.
* **ML is trained on synthetic data.** Synthetic-split scores (1.00) are meaningless as performance claims. The hand-written held-out sets are small (80 and 42 items; 5 per misconception) and were written by the same team, so results (misconception production path P 0.90 / R 0.71 / F1 0.79; behaviour classifier F1 0.73) are indicative only. Behaviour rules-plus-ML is *worse* than ML alone on that set.
* **The success model is fitted to a simulated process**, i.e. to our own assumptions. It is a prior for matching difficulty, not a validated predictor. Mastery uses BKT with fixed, un-fitted parameters.
* The fingerprint's weights/values (e.g. safe 90 / mixed 55 / unsafe 15) are design choices documented in `docs/SCENARIO_ENGINE.md`, not empirically calibrated.

## Language and AI
* The **local 3B LLM is used in English only** (measured Hindi was broken; Hinglish drifted to English). It contributes one optional coach note and optional rephrasing of retrieved Q&A. Everything else in Hindi/Hinglish is curated text.
* **Hindi (Devanagari)** is complete for the UI, concept explanations, safety messages and the hero scenario. The other seven scenarios have Hinglish (Roman script) only; Hindi mode shows that Hinglish text. Quiz questions are English only. Hinglish TTS uses the English voice.
* Regional languages beyond Hindi/Hinglish are *architecturally* supported (a new column in `lib/i18n.ts`, a new overlay key per scenario, a new Piper voice) but not implemented.
* The Safety Gateway is pattern-based; creative phrasing, transliteration variants or other scripts can slip past the input check (outputs are still template/retrieved text). It has 99 adversarial/benign tests, not a formal guarantee.
* Speech recognition accuracy for accented Hindi/Hinglish with Whisper-base was **not** evaluated; only an English round trip was verified.

## Content
* The **knowledge base is project-authored**, not official regulator material (flagged `verified_official: false` and shown as such). Pointers such as the 1930 helpline / cybercrime portal and "verify registration on the regulator's site" are general and should be re-checked against current official sources before any public release.
* Scenarios are plausible fiction, reviewed by the engineering team only — not by compliance, legal, or financial-education experts.

## Engineering
* Single-user local app: no authentication beyond an anonymous token; do not expose it publicly. SQLite only.
* Playwright tests run in Microsoft Edge (Chromium download from the Playwright CDN timed out on the dev machine); Firefox/WebKit were not tested. The mobile layout was checked at 375–390 px in a Chromium emulation, not on physical devices.
* The Next.js production build is required for the launcher (built once automatically). Windows is the only OS the full stack was exercised on; the code avoids OS-specific APIs except the launcher's `taskkill`.
* `onnxruntime` crashes the interpreter if imported after scikit-learn on the dev machine, so speech runs in an isolated worker process (see AI.md). Other machines may not have this problem; the isolation is harmless there.
* Embedding model and Whisper model files are downloaded once on first use / setup; "offline after installation" holds only after those downloads have happened (the core simulator never needs them).

## Audit results (Phase 24)
* No API keys, tokens, credentials or `.env` files are tracked in git (pattern scan + tracked-file listing). The only tracked binaries are the three small scikit-learn model files (≈ 0.8 MB), which contain no personal data.
* No log statement records learner text, transcripts or tokens.
* The database schema has no PII columns (tested), reasoning text is redacted before storage (tested), and export/reset/delete work end to end (tested).
