# ARCHITECTURE.md — ARTHDARSHAN

*Train before you face it.* An educational financial-decision-resilience simulator. It gives no investment advice. All scenarios are fictional and use no real money.

## Core principle: three layers with strict separation

| Layer | Owns | Never does |
|---|---|---|
| **Deterministic engine** | Scenario truth, state transitions, consequences, pressure, scoring rules | Call an LLM to decide what happens |
| **Classical ML** | Misconception/behaviour classification, mastery estimation, adaptive scenario selection | Run without an evaluated, versioned model or a rule fallback |
| **LLM / RAG (optional)** | Plain-language explanation, reasoning feedback, Q&A with citations, voice | Control scenario state, or emit unfiltered text |

If the ML or LLM layers are unavailable, the product still runs end to end on the deterministic layer plus rule-based fallbacks.

## System diagram

```
Browser (Next.js + TS + Tailwind)  ── offline-capable core, Web Speech fallback
        │  HTTPS-free localhost REST
        ▼
FastAPI (apps/api)  ── Pydantic validation, logging, error handling
        │
        ├── Safety Gateway (ai/safety)      ← wraps EVERY user input and EVERY AI output
        ├── Scenario Engine (ai/scenario_engine)   deterministic state machine
        ├── Misconception Engine (ai/misconception) rules + trained classifier
        ├── Adaptive Learning (ai/adaptive_learning) transparent weakness→training policy
        ├── Resilience scoring (fingerprint, 10 dimensions)
        ├── Simulations (simulations/)      fee, compounding, concentration, volatility…
        ├── RAG (ai/rag)                    embeddings → fallback BM25/keyword
        ├── LLM (ai/llm)                    Ollama → fallback templates
        └── Voice                           faster-whisper / Piper → browser → text
        │
        ▼
SQLite (database/) via SQLAlchemy + Alembic migrations
```

## Request flow for a decision

```
POST /api/decisions
  → Safety: check free-text reasoning (PII/credential patterns, advice requests)
  → Scenario engine: validate action is legal in current state; apply transition; produce consequence + new evidence + pressure
  → Persist decision + reasoning + latency + confidence + evidence requested/ignored
  → Misconception engine: classify reasoning + choice → detected misconception ids (with confidence and source)
  → Scoring: update fingerprint dimensions from explicit scoring rules
  → Adaptive: update mastery, choose next scenario with a logged, human-readable rationale
  → Explanation: LLM if available, else template; Safety output check
  → Response
```

## Scenario engine

A scenario is data (JSON/YAML in `configs/scenarios/`), validated against a schema: metadata, concept tags, difficulty, initial state, actions, pressure config, evidence, transitions, consequences, reflection, scoring rules. The engine is a pure function `(scenario, state, action) → (state', consequence, evidence, pressure)` with no randomness unless seeded. Transition coverage is unit tested for every scenario (all states reachable, all actions defined, terminal states reach reflection). Details in `docs/SCENARIO_ENGINE.md` (written in Phase 3).

## Resilience fingerprint

Ten dimensions scored 0–100 from explicit, documented rules over recorded decision data (e.g., FOMO Resistance falls when the user acts under scarcity/countdown pressure without requesting evidence). Scores are smoothed over attempts. Language is non-judgmental by construction (template review plus safety output check).

## Misconception engine (M001–M012)

1. Rule signals from choices and evidence ignored (high precision).
2. Text classifier over reasoning (embeddings or TF-IDF + logistic regression) trained on **clearly labelled synthetic data**; evaluated with precision/recall/F1/confusion matrix on a held-out split. Metrics are written to `artifacts/` by the evaluation script, never hand-entered.
3. Detections stored in `user_misconceptions` with status over time (detected → improving → resolved).

## Adaptive learning

A transparent policy: weakest dimensions and unresolved misconceptions map to scenario/pressure/simulation tags; next scenario = highest tag overlap at difficulty adjusted by mastery estimate. Every selection stores weakness, chosen training, difficulty, outcome and mastery in the DB, and the rationale string is shown to the user. A learned mastery model may be layered on later, always with the rule policy as fallback.

## Safety Gateway (`ai/safety`)

Input check → processing → output check. Detects advice/buy-sell-hold, price prediction, personalized advice, broker/product promotion, sensitive data (OTP, PIN, card, Aadhaar, PAN, passwords), unsupported regulatory claims, and ungrounded facts. On violation: block or rewrite to a safe educational response. Scenario content is also linted at load time. Adversarial test suite required in CI. See `docs/SAFETY.md` (Phase 13).

## RAG

Documents → chunks → embeddings, stored with source, title, date, chunk, metadata in `knowledge_documents` / `knowledge_chunks`. Answers carry internal citations. If retrieval support is insufficient the system answers: *"I don't have enough verified information to establish that."* Only user-supplied or clearly sourced public educational material is ingested; nothing regulatory is written from memory.

## Data and privacy

SQLite on the local machine; pseudonymous learner profile (display name optional, no PII fields). No financial identifiers are accepted. Delete/reset learner data endpoint and UI. Details in `docs/PRIVACY.md`.

## Offline and degradation matrix

| Component down | Behaviour |
|---|---|
| LLM | Deterministic explanation templates |
| Embeddings | BM25/keyword retrieval |
| STT / TTS | Browser speech APIs, then text |
| Classifier model missing | Rule-based misconception signals |
| Network | Entire core works (all assets served locally) |

## Repository layout

```
apps/web  apps/api   ai/{llm,rag,safety,misconception,adaptive_learning,scenario_engine}
ml/{datasets,training,evaluation,models}   data/{raw,synthetic,processed,knowledge_base}
simulations  database  scripts  tests  docs  artifacts  configs
```

## Decisions made autonomously (and why)

- **Own git repo inside `arthdarshan/`:** the surrounding git root is the user's home directory.
- **SQLite + Alembic**, no Postgres: single-user local demo.
- **Small local LLM (3B Q4) as optional layer**, templates as the guaranteed path: 6 GB VRAM machine (see `HARDWARE.md`).
- **Scenarios as validated data, engine as pure function:** testable and keeps LLM out of scenario truth.
- **No microservices:** one FastAPI process importing the `ai/*` packages.

## Build phases

Phases 0–18 as defined in the project brief. Status: Phase 0 complete, Phase 1 in progress.
