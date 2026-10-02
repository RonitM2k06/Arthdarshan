# ARTHDARSHAN — *Train before you face it.*

An **AI-assisted financial decision-resilience simulator** built for the SANGYAN Investor Resilience Hackathon 2026 (Track C — Investor Education for Bharat).

It is a *flight simulator for financial decisions*. You step into a realistic **fictional** situation (a "guaranteed 30%" Telegram message, a market crash, a confusing fund summary…), decide under pressure, see the consequence, and get honest feedback on **how** you decided — which warning signs you noticed, how pressure moved you, which misconceptions showed up — not just which option you picked.

> **SIMULATED · NO REAL MONEY · FICTIONAL.** ARTHDARSHAN never recommends what to buy, sell or hold, never predicts prices, never asks for OTPs/PINs/passwords/Aadhaar/PAN, and never touches real money. A rule-based safety gateway enforces this on every input and every AI output.

## What is in the box

| Area | What exists and works |
|---|---|
| **Scenarios** | 8 playable branching scenarios (guaranteed-return scam, WhatsApp "expert", market shock, concentration, hidden fee, urgent FOMO decision, confusing document, family file), run by a deterministic state machine |
| **Pressure engine** | urgency, countdown, scarcity, social proof, authority, FOMO, fear, greed, loss-recovery, peer pressure — configured per state, reactions recorded |
| **Fingerprint** | 10-dimension Financial Resilience Fingerprint computed *only* from your recorded decisions (score, previous, change, evidence) |
| **Misconceptions** | M001–M013, rules + locally trained classifier + choice signals; tracked active → improving → resolved |
| **Adaptive learning** | transparent weakness → training policy with Bayesian Knowledge Tracing mastery; every recommendation lists its reasons |
| **Simulations** | 9 interactive zero-money simulations (fees, compounding, inflation, concentration, diversification, volatility, liquidity, emergency savings, scam-loss progression) |
| **Knowledge** | 22-concept graph (simple/detailed/examples/related/misconceptions/quiz), Evidence Lab, local RAG with citations |
| **Voice & languages** | English / Hindi / Hinglish UI and scenario text; local Piper TTS + faster-whisper STT with browser/text fallbacks |
| **Local AI** | optional Ollama model (Qwen2.5-3B Q4) used for a short English coach note and grounded Q&A; everything works without it |
| **Accessibility** | Simple Mode (large text, high contrast, fewer choices, confirmations, no timers, read-aloud), automated axe checks |
| **Privacy** | local SQLite, no accounts, no PII, one-tap export / delete |

## Quick start (Windows / macOS / Linux)

Requirements: Python 3.11+, Node 18+. Optional: Ollama, GPU.

```bash
# 1. one-time setup (core only, no big downloads): python deps, DB migrations, ML models, web build
python scripts/setup.py
#    optional extras
python scripts/setup.py --voice      # local TTS/STT libs + two small Piper voices (~130 MB)
python scripts/setup.py --llm        # pulls qwen2.5:3b-instruct (~2 GB) through Ollama (must be installed)

# 2. launch everything and open the hero journey
python scripts/demo.py
```

`python scripts/demo.py` starts the API (http://127.0.0.1:8000, docs at `/docs`) and the web app (http://localhost:3000) and opens **THE GUARANTEED OPPORTUNITY**. Flags: `--dev` (hot reload), `--no-browser`, `--low-resource` (no LLM / embeddings / STT).
On the landing page, **"See a sample learner's fingerprint"** loads a *scripted* persona whose decisions ran through the real engine (clearly labelled as scripted).

### Manual commands

```bash
pip install -r requirements.txt
python scripts/build_knowledge.py && python scripts/build_scenarios.py   # compile + validate content
python scripts/migrate.py                                                # alembic upgrade head + content sync
uvicorn apps.api.main:app --port 8000                                    # API
cd apps/web && npm install && npm run build && npm run start             # web (or: npm run dev)
```

## Testing

```bash
python -m pytest                          # backend: engine, safety, ML, API, simulations, adaptive, voice, migrations
cd apps/web && npm test                   # frontend unit tests (Vitest)
cd apps/web && npx playwright test        # end-to-end + accessibility (axe). Uses Edge by default; PW_CHANNEL=chrome to change
```

Results from the last full run are in [docs/TESTING.md](docs/TESTING.md).

## ML training and evaluation

```bash
python -m ml.training.train               # regenerates SYNTHETIC datasets, trains 3 models, evaluates, writes metrics
```
Writes `ml/models/*.joblib`, `ml/evaluation/*_metrics.json`, `artifacts/ml_metrics.json`, and registers model versions/training runs in the DB. Metrics are produced by the script; none are typed by hand. See [docs/ML.md](docs/ML.md) for what they do and do **not** show.

## Optional local AI setup

1. Install Ollama (https://ollama.com), then `ollama pull qwen2.5:3b-instruct`.
2. `python scripts/demo.py` starts Ollama if needed, warms the model, and the Settings page shows what is active.
3. Without Ollama everything still works; explanations come from deterministic templates.

Environment variables (prefix `ARTH_`, see `.env.example`): `LOW_RESOURCE`, `LLM_ENABLED`, `LLM_MODEL`, `ENABLE_EMBEDDINGS`, `DATABASE_URL`.

## Documentation

[ARCHITECTURE](docs/ARCHITECTURE.md) · [AI](docs/AI.md) · [ML](docs/ML.md) · [SCENARIO_ENGINE](docs/SCENARIO_ENGINE.md) · [SAFETY](docs/SAFETY.md) · [PRIVACY](docs/PRIVACY.md) · [HARDWARE](docs/HARDWARE.md) · [DEMO_SCRIPT](docs/DEMO_SCRIPT.md) · [PITCH](docs/PITCH.md) · [TESTING](docs/TESTING.md) · [LIMITATIONS](docs/LIMITATIONS.md)

## Honest limitations (short list; full list in docs/LIMITATIONS.md)

* ML models are trained on **synthetic** data (labelled as such); the hand-written held-out set has only 80 / 42 items.
* The local 3B LLM is used **only in English**; its Hindi was measured to be unreliable, so Hindi/Hinglish text is curated, not generated.
* Hindi translation covers the UI, concepts and the hero scenario; the other seven scenarios have Hinglish (Roman-script) overlays and fall back to it for Hindi.
* The knowledge base is **project-authored** educational text, not official regulator publications (it says so wherever it is cited).
* Not a substitute for professional advice; no claim about real-world outcomes is made.
