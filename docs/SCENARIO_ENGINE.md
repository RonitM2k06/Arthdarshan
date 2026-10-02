# SCENARIO_ENGINE.md

A scenario is **validated data** (`configs/scenarios/*.json`, compiled from the authoring format in `configs/scenario_src/`). The engine (`ai/scenario_engine/engine.py`) is a set of **pure functions** — no LLM, no unseeded randomness, no mutation. Scenario truth lives only here.

```
STATE ──(learner action)──▶ STATE′ + consequence + new evidence + new pressure … ──▶ TERMINAL ──▶ REFLECTION
```

## Schema (`ai/scenario_engine/schema.py`, Pydantic, `extra=forbid`)

`Scenario` = metadata (id, version, title, tagline, character) · `difficulty` 1–3 · `concept_tags` · `pressure_tags` · `tests_misconceptions` (first = primary focus) · `initial_state` · `states{}` · `reflection` (key points, questions, micro-lesson) · `scoring` (dimensions trained; first = primary) · `i18n` overlays · `disclaimer` (must contain *NO REAL MONEY*).

`State` = narrative · `channel` (telegram/whatsapp/app/news/document/call/… with sender and messages) · `pressure[]` (type, text, optional `countdown_seconds`, intensity 1–3) · `evidence[]` (id, label, text, **kind** red_flag/neutral/reassuring/missing_info, **why**) · `actions[]` · optional `terminal` + `outcome`.

`Action` = id · label · **quality** safe/mixed/unsafe · `next` (the explicit transition) · `consequence` · `verification` (True = verified independently, False = skipped an available check) · `requests_evidence` · `misconception_signals` · explicit scoring `observations` · `concept_tags` · short `simple_label` for Simple Mode.

## Validation (`validate_scenario`) — run at build time, at load time, and before every session starts

* initial state exists; every `next` exists; keys match ids; no duplicate action/evidence ids
* every state reachable from the start, and **every state can reach a terminal state** (no dead loops)
* terminal states have an outcome and no actions; non-terminal states have ≥ 2 actions and ≥ 1 *safe* action (each decision has a defensible path)
* red-flag evidence must carry a `why`; countdown pressure needs `countdown_seconds`
* known concepts, misconception ids, dimensions and pressure types only
* **safety lint:** no text that requests OTP/PIN/CVV/password/Aadhaar/PAN, none that reads like advice ("you should buy…", "best stock"), disclaimer states NO REAL MONEY

## Execution

`step(scenario, state, action, evidence_noticed)` → `StepResult` (next state, consequence, terminal flag, evidence recall, misconception signals, observations, pressure types, countdown). Unknown actions/states raise typed errors (→ HTTP 400/409). The client never sees evidence classification, quality or "why" *before* deciding (`public_state_view`), which is what makes it a simulator rather than a quiz with the answer key visible.

**Evidence recall** = red flags the learner marked ÷ red flags present; marking a reassuring item is recorded as a "false alarm" and not penalised.

## Scoring rules (`apps/api/services/scoring.py`)

Each decision emits explicit `(dimension, value 0–100, weight, note)` observations; a dimension's score is a recency-weighted average (decay 0.9 per observation) with a weak prior of 50 at weight 1; dimensions with no observations are reported as **not measured** (never invented).

| Observation source | Dimension | Value |
|---|---|---|
| response to pressure types in the state (urgency/countdown/scarcity/FOMO → FOMO resistance; social proof/peer → herd resistance; fear/greed/loss-recovery → emotional discipline; authority → evidence verification) | per type | safe 90 / mixed 55 / unsafe 15 (−10 if unsafe and decided < 4 s) |
| warning signs noticed | risk recognition | 0.7·recall + 0.3·quality |
| verification action | evidence verification | verified 92 · skipped 15 · asked the source 70 |
| scam scenarios | scam awareness | 0.6·quality + 0.4·recall |
| reasoning text | independent reasoning | evidence-based 85 · relied on others 20 · misconception text 30 |
| stated confidence vs quality; acknowledged uncertainty; overconfident phrasing | uncertainty awareness | high-confidence-and-wrong 15 … acknowledged 85 |
| stated emotion + unsafe choice / pause or calm | emotional discipline | 20 / 85 |
| scenario-declared checks, quiz answers | terminology / concept knowledge | 10–92 |

## The eight scenarios

| id | focus | states / actions / endings |
|---|---|---|
| guaranteed_opportunity (hero) | scams, guaranteed returns, urgency, verification | 14 / 21 / 8 |
| whatsapp_expert | social proof, misinformation, past performance | 12 / 17 / 7 |
| market_shock | volatility, panic, uncertainty (fictional index) | 6 / 9 / 4 |
| one_basket | diversification vs concentration (numbers computed in code) | 10 / 19 / 4 |
| hidden_fee | fees, net outcomes, disclosures (numbers computed in code) | 6 / 12 / 3 |
| urgent_decision | FOMO, scarcity, escalating countdowns | 6 / 11 / 3 |
| confusing_document | NAV, exit load, indicative yield, plain language | 7 / 16 / 2 |
| family_file | nomination, preparedness, KYC call, recovery scam, rights | 9 / 14 / 5 |

Every fictional entity, number and message is fictional; consequences and loss figures are labelled simulated.

## Tests

`tests/test_scenario_engine.py` (40 cases): all eight validate; **every (state, action) edge of every scenario executes**; each scenario has a safe ending and at least two outcome kinds; the hero branches exactly as in the brief (invest → ₹2,000 fee; verify → registration claim; investigate → evidence; walk → end); determinism; evidence recall; the public view never leaks the answer key; validator negative tests (dangling transition, unreachable state, dead loop, missing outcome, no safe action, credential request, advice); localisation overlays; all ten pressure types are used somewhere. `tests/test_api.py` additionally plays every scenario through the API (first-safe path and four seeded random walks each) and asserts termination.
