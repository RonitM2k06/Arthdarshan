# ARCHITECTURE.md — ARTHDARSHAN

*Train before you face it.* An educational financial-decision-resilience simulator. No investment advice, no real money, everything local.

## Separation of concerns

| Layer | Owns | Never does |
|---|---|---|
| **Deterministic engine** (`ai/scenario_engine`) | scenario truth, transitions, consequences, pressure, validity | call an LLM |
| **Scoring** (`apps/api/services/scoring.py`) | fingerprint from explicit, documented rules over recorded data | invent a score for an unmeasured dimension |
| **Classical ML** (`ai/misconception`, `ml/`) | misconception & behaviour classification, success prediction | run without a rule fallback |
| **Adaptive policy** (`ai/adaptive_learning`) | weakness → training selection with a reasons list; BKT mastery | act as a black box |
| **Local LLM** (`ai/llm`, optional) | one English coach note; rephrasing of retrieved Q&A | state scenario facts, control state |
| **RAG** (`ai/rag`) | retrieval + citations; refuses without evidence | fabricate sources or rules |
| **Safety gateway** (`ai/safety`) | input/output validation, redaction, blocking | depend on any model |

## System

```
Browser — Next.js 14 + TypeScript + Tailwind (served locally; proxies /api → FastAPI; no external assets)
   │  Web Speech API fallback for voice
   ▼
FastAPI (apps/api) — Pydantic (extra=forbid), uniform safe errors, logging without learner text
   ├─ routers: auth · users · scenarios · decisions · reflection · simulations · learning · concepts · progress · resilience · rag · voice · safety · models · health
   ├─ Safety gateway ──────────── wraps every input and output
   ├─ Scenario engine ─────────── pure functions over validated JSON (configs/scenarios)
   ├─ Misconception + behaviour ─ rules → trained classifiers (gated) → choice signals
   ├─ Scoring / fingerprint ───── observations → recency-weighted scores → snapshots
   ├─ Adaptive learning ───────── BKT + transparent selection policy (+ success model)
   ├─ Simulations (simulations/) ─ 9 deterministic zero-money models
   ├─ RAG ─────────────────────── MiniLM embeddings + BM25, keyword fallback
   ├─ LLM client ──────────────── Ollama (Qwen2.5-3B Q4), lazy, time-limited, validated
   └─ Voice client ── RPC ──▶ isolated worker process: Piper TTS + faster-whisper STT
   ▼
SQLite (SQLAlchemy 2 + Alembic) — 19 required tables + sessions/observations/selections
```

## Decision pipeline (`POST /api/decisions`)

```
validate request → ownership/state checks (404/409)
→ SAFETY on free text (mask PAN/Aadhaar/OTP/…; flag advice-seeking)
→ ENGINE.step (truth: quality, next state, consequence, evidence recall, pressure)
→ ANALYSIS: misconception rules + ML (gated) + choice signals; behaviour rules + ML + context; emotions; uncertainty
→ PERSIST decision + reasoning (+ per-dimension observations; concept mastery via BKT; misconception counters)
→ EXPLAIN: deterministic template; optional English coach note (validated, safety-checked)
→ response (consequence, analysis, next state) — or, on a terminal state:
   FINALIZE: summary, fingerprint snapshot (previous/change), misconception exposures (active→improving→resolved),
             adaptive selection (stored with weakness, difficulty, mastery estimate, rationale), micro-lesson, reflection
```

## Data model (`database/models.py`)
`users · concepts · user_concepts · scenarios · scenario_states · scenario_sessions · scenario_decisions · decision_reasoning · misconceptions · user_misconceptions · lessons · quiz_questions · quiz_attempts · simulations · simulation_events · dimension_observations · resilience_scores · adaptive_selections · model_versions · training_runs · knowledge_documents · knowledge_chunks` with foreign keys (enforced in SQLite), cascade deletes for learner data, check constraints (language, confidence range, mastery range, observation range) and indexes on the hot lookups. Migrations live in `database/migrations` (tested up and down).

## Offline / degradation matrix

| Component unavailable | Behaviour |
|---|---|
| internet | no change — all assets, models and data are local |
| LLM | templates; no coach note; extractive Q&A |
| embeddings | BM25 keyword retrieval |
| Piper / Whisper | browser speech → plain text |
| trained classifiers | rules + choice signals; heuristic difficulty fit |
| database error | safe 503 JSON, no internals leaked |
| `ARTH_LOW_RESOURCE=1` | LLM, embeddings and STT off; still plays every scenario |

## Key engineering decisions (and why)
* **Own git repo in `arthdarshan/`** — the surrounding git root is the user's home directory.
* **Scenarios are data, the engine is pure** — testable exhaustively (every edge executed in CI) and keeps the LLM out of truth.
* **LLM demoted to an optional note** after a live test showed a fluent but factually inverted sentence; factual explanation is template-based.
* **Voice in a separate process** — importing `onnxruntime` after scikit-learn segfaults on the dev machine; process isolation removes an uncatchable crash from the API.
* **Production detector = rules + gated ML** — measured to beat either alone on the held-out set.
* **SQLite + Alembic, one process, no microservices** — single-user local product.
* **Hand-written held-out sets** and metrics produced by scripts — so no performance claim is typed by hand.
