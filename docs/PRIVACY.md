# PRIVACY.md

ARTHDARSHAN is privacy-first by construction: it runs on the learner's own machine and has no reason to know who they are.

## Exactly what is stored (SQLite, `database/arthdarshan.db`, on this machine only)

| Table(s) | Contents |
|---|---|
| `users` | random UUID, SHA-256 hash of a random token, optional display name (≤ 40 chars, may be fictional), language, simple-mode flag, streak counters. **No email, phone, address, real-name, age or location fields exist in the schema** (tested). |
| `scenario_sessions`, `scenario_decisions`, `decision_reasoning` | which scenario/action, response time, confidence 1–5, warning signs marked, pressure present, and the reasoning text the learner typed/spoke — **after** sensitive-looking values (PAN, Aadhaar, OTP, PIN, password, card number, UPI ID, account number, IFSC) are masked as `[REDACTED]` |
| `dimension_observations`, `resilience_scores` | the numbers behind the fingerprint, each with a human-readable note |
| `user_concepts`, `user_misconceptions`, `quiz_attempts`, `simulation_events`, `adaptive_selections` | derived learning state |
| `knowledge_*`, `concepts`, `scenarios`, … | static content, no personal data |

The learner's browser stores the profile token and UI preferences (language, simple mode) in `localStorage`.

## What is never collected or sent

* OTPs, PINs, passwords, card numbers, Aadhaar, PAN, bank or brokerage details — never requested; if typed they are masked before storage and the learner is told.
* Anything to a third party: the language model, embeddings, speech recognition, speech synthesis and retrieval all run locally; the web app loads no external scripts, fonts or analytics (an end-to-end test of the landing page fails if any request leaves localhost). The only network use is the one-time optional download of models during setup.
* Logs: the API log (`artifacts/logs/api.log`) records events and error types, **never** reasoning text or tokens; error responses never include stack traces or internals.

## Control

* **Settings → Download my data** (`GET /api/users/me/export`): everything above for this profile as JSON.
* **Settings → Delete my learning data** (`DELETE /api/users/me/data`): removes sessions, decisions, reasoning, observations, scores, concepts, misconceptions, quiz and simulation history; keeps the empty profile.
* **Settings → Delete my profile completely** (`DELETE /api/users/me`): removes everything including the profile; the token stops working.
* Deletion is immediate and permanent (tested end to end, including cascade of decisions/reasoning).

## Security notes

* Anonymous bearer token (`secrets.token_urlsafe(32)`), stored only as a hash. Sessions are scoped to their owner (another profile gets 404).
* Strict Pydantic validation with `extra=forbid` on every request body; bounded text, list and number sizes; safe error envelope; parameterised queries via SQLAlchemy.
* No secrets in the repository (see `.env.example`, `.gitignore`); `docs/LIMITATIONS.md` lists the audit result.
* This is a local single-user demo server; it binds to `127.0.0.1` and has no authentication beyond the profile token. Do not expose it to a network as-is.
