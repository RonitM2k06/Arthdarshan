# DEMO_SCRIPT.md — a 4–5 minute walkthrough

**Setup (before judging):** `python scripts/demo.py` — wait for "ARTHDARSHAN is running". Everything is local; no internet, API keys or sign-up. (If asked about the first start: the API takes ~10 s to warm the local model.) Backup if anything misbehaves: `python scripts/demo.py --low-resource`.

| # | Time | Do / show | Say |
|---|---|---|---|
| 1 | 0:00 | Landing page (http://localhost:3000). Point at the hero card on the right. | "ARTHDARSHAN — *Train before you face it.* A flight simulator for financial decisions. It doesn't tell you what to invest in. It trains how you decide." |
| 2 | 0:20 | Click **ENTER SIMULATOR** → **Start** on *The Guaranteed Opportunity* (or open `/demo`). | "Rahul, 24, first job. A stranger adds him to Telegram. Note the badge: simulated, no real money, fictional." |
| 3 | 0:40 | Show the message, the pressure strip (countdown, scarcity, urgency) and the evidence cards. Tick *Guaranteed 30% returns* only. | "Pressure is explicit and configurable. I can mark what looks suspicious — I'll only catch one." |
| 4 | 1:00 | Choose **Invest now**; type *"My friend invested so it is probably legit and it is guaranteed"*; confidence 5; **Decide**. | "No 'correct answer' banner. Watch what happens." |
| 5 | 1:20 | Read the consequence (₹6,500 "profit"). Show **How you decided**: warning signs recognised vs missed (with *why*), pattern **RELIANCE ON A PERSONAL RECOMMENDATION**, misconceptions **M011, M001**, response-time under pressure, the optional *Local AI note*. | "Deterministic engine owns the truth; classifiers found the misconceptions; the local model only comments on my own words. Not judgemental." |
| 6 | 2:00 | **Continue** → ₹2,000 "verification fee" with loss-recovery pressure. Choose **Stop and check whether this company really exists**. Mark red flags in the investigation notes → **Leave, keep screenshots and report**. | "Second decision, new pressure, new evidence. Now the verification habit." |
| 7 | 2:40 | Summary: outcome, **fingerprint** (note *Not measured yet* for dimensions without data), strengths/opportunities, micro-lesson, **Your next training** → *Why this one?* | "Every score comes from my decisions — unmeasured dimensions say so. The next scenario is chosen transparently: here are the reasons and weights." |
| 8 | 3:10 | Start the recommended scenario (*The Urgent Decision*) and make a calmer choice; show the **▲ change** and improvement trend on **My Resilience**. Or click *See a sample learner* on the landing page for a populated report (labelled scripted). | "Improvement over time, evidence behind each score, behavioural patterns, misconception status active → improving → resolved." |
| 9 | 3:40 | Header language menu → **हिन्दी** / **Hinglish**; **Aa** for Simple Mode (big text, confirmation step, no timer). Then **Learn → Ask (voice)**: type or speak *"Volatility kya hoti hai?"* → spoken Hinglish answer with sources. | "Hindi, Hinglish, voice, and an accessibility-first Simple Mode for seniors and first-time users. The model and voices run locally." |
| 10 | 4:10 | **Learn → Safety demo**: click *What stock should I buy tomorrow?* and *Predict NIFTY tomorrow.* Then *Run* the output check. | "It won't recommend, predict, or take your OTP — a real gateway, tested on adversarial prompts, with educational redirects." |
| 11 | 4:35 | Close on the landing sentence. | **"ARTHDARSHAN doesn't tell you what to invest in. It trains you to think before you decide."** |

## If a judge asks…
* *"Is the LLM making things up?"* — It never decides or states scenario facts; templates do. It writes one optional English note on the learner's own words; every output is validated and safety-checked, and the app is identical without it (Settings shows what is active).
* *"Where do the ML numbers come from?"* — `python -m ml.training.train` writes them; docs/ML.md shows synthetic-split vs hand-written held-out vs production path, and says which are optimistic.
* *"Offline?"* — Stop Wi-Fi; the simulator, scoring, learning, simulations, safety, Hindi/Hinglish, and (if installed) voice all keep working.
* *"Is the data real?"* — The sample learner is scripted (labelled) but runs through the real engine; knowledge notes are project-authored and labelled non-official.
