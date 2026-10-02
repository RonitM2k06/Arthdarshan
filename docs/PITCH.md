# PITCH.md — ARTHDARSHAN

## One line
**A flight simulator for financial decisions: it trains how Bharat's first-time and vulnerable investors decide under pressure — without ever telling them what to invest in.**

## The problem (Track C — Investor Education for Bharat)
People who lose money to scams, panic or FOMO usually *knew* the definitions. What they lacked was practice facing a countdown, a crowd, a confident stranger or a trusted friend. Static quizzes and explainers don't build that. Regulators and educators also cannot — and should not — hand out advice, so tools that "recommend" are off the table.

## The idea
Put the learner **inside** a realistic fictional situation → decision → consequence → new pressure/evidence → second decision → analysis of **how** they decided → targeted micro-training → a new scenario. Measure *judgement*, not recall: which warning signs were noticed, whether they verified independently, how urgency/social proof/authority moved them, which misconceptions appeared.

## What makes it different
1. **Behaviour, not trivia** — a 10-dimension *Financial Resilience Fingerprint* computed only from the learner's recorded decisions (unmeasured = "not measured yet", never invented), with previous/change and the evidence behind every number.
2. **Deterministic truth + AI as assistant** — a validated state machine owns scenarios and consequences; classical ML finds misconceptions; a small local LLM adds an optional note; a rule-based **safety gateway** enforces "no advice, no predictions, no credentials" on every input and output.
3. **Built for Bharat** — English / Hindi / Hinglish, voice in and out (local Piper + Whisper), an accessibility-first **Simple Mode**, works **offline** on a laptop; no accounts, no PII, one-tap erase.
4. **Transparent adaptation** — every "next training" shows its reasons (weakness, pressure types, difficulty fit); mastery is Bayesian Knowledge Tracing, not a black box.
5. **Zero-money consequence labs** — nine interactive simulations (fee erosion, compounding, inflation, concentration, diversification, volatility, liquidity, emergency savings, scam-loss progression), all labelled illustrative.

## Demo (see DEMO_SCRIPT.md)
Rahul's "guaranteed 30%" Telegram message → impulsive path, fee demand, loss-recovery spiral → analysis (friend-reliance, M001/M011/M010) → careful replay → fingerprint ▲ → Hinglish voice Q&A → safety gateway blocking *"What stock should I buy tomorrow?"*.

## Engineering credibility
* 8 scenarios, 14-state hero, all validated; every transition tested. 292 backend + 20 frontend + 33 browser/accessibility tests passing.
* Local ML trained and evaluated reproducibly (precision/recall/F1/confusion). On a hand-written held-out set the production misconception detector reaches P 0.90 / R 0.71 / F1 0.79 versus 0.40 F1 for rules alone — reported alongside the fact that synthetic-split scores are optimistic.
* Runs on a 6 GB-VRAM laptop: Qwen2.5-3B-Q4 (optional), MiniLM embeddings, Piper, Whisper-base. A voice crash-risk was found (native-library clash) and engineered around with process isolation. Where a model was not good enough (3B Hindi) it was **disabled**, not shipped.

## Impact for SEBI / NSDL-style investor education
Deployable at kiosks, schools, senior-citizen centres and community workshops with no connectivity and no data leaving the device; content is plain JSON so educators can add scenarios (and regional languages) without code; the product's guardrails are explicit and auditable.

## Honest status and roadmap
* Today: working prototype, synthetic-data ML, English-only LLM, Hindi complete for UI/concepts/hero scenario, Hinglish for all scenarios.
* Next: pilot with real learners and educators (consent-based local logs to refit the success model and calibrate the fingerprint), expert review of scenario content, official source ingestion into the RAG store, more Indian languages, physical-device accessibility testing.

> *ARTHDARSHAN doesn't tell you what to invest in. It trains you to think before you decide.*
