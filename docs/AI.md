# AI.md — the local AI layer

**Principle: the AI enhances the simulator; it never replaces deterministic logic.**

| Layer | Owns | Never does |
|---|---|---|
| Deterministic engine | scenario truth, transitions, consequences, pressure, scoring rules | call an LLM |
| Classical ML | misconception / behaviour classification, success prediction | run without a rule fallback |
| Local LLM (optional) | a short English *coach note* on the learner's own words; grounded Q&A text | control state, scores, or state facts about a scenario |
| RAG | retrieval of educational notes with citations | invent citations or regulatory claims |
| Safety gateway | input/output validation, blocking, redaction | depend on any model |

No cloud API is part of the runtime. Claude Code was only the development agent.

## Local LLM

* **Model:** Qwen2.5-3B-Instruct, 4-bit, served by Ollama (≈ 2 GB VRAM/RAM; fits the 6 GB RTX 4050). Chosen for the hardware (see HARDWARE.md); no larger model is downloaded.
* **Lifecycle:** lazy. `ai/llm/client.py` detects Ollama and the model (cached 10 s, never raises), warms the model in a background thread at server start so the first learner is not a cold start (measured: a cold first call exceeded the 25 s timeout and correctly fell back to templates), and unloads after 10 minutes idle (`keep_alive`).
* **Timeout & fallback:** every call is time-limited; on any failure the response is simply the deterministic one.
* **Structured output:** the model must reply JSON; the parser tolerates stray text; anything else is dropped.

### What the LLM is allowed to do — and why that is narrow

During live testing the 3B model turned "the sender *claims* SEBI registration" into "it *lacks* registration" — fluent, plausible, wrong, and it passed every mechanical check. So factual explanation of a decision (what you noticed, what you missed, which pattern, the correction) is **always produced by templates from the engine's computed facts** (`ai/llm/templates.py`, in all three languages).

The LLM may add one optional **"Local AI note on your reasoning"**: one or two sentences reflecting something specific in the learner's own words and suggesting an independent-verification habit. Guards (`ai/llm/explainer.py`): English only; needs ≥ 15 characters of reasoning; JSON with length 20–360; no numbers that are not in the learner's text; language check; rejects sentences asserting facts about the scenario ("lacks", "is a scam", …); must pass the Safety Gateway. Reject → no note, nothing else changes. Measured: English notes in ≈ 0.7 s warm.

**Hindi and Hinglish:** tested, and the 3B model's Hindi was visibly broken and its Hinglish drifted to English. Rather than ship that, the LLM is disabled for those languages; they use curated templates, concept text and scenario overlays written by us.

## Local RAG (`ai/rag/engine.py`)

* **Store:** `knowledge_documents` (title, source, source_type, `verified_official`, date, language, content hash, metadata) and `knowledge_chunks` (text, embedding bytes, model, metadata).
* **Sources:** 14 short educational notes in `data/knowledge_base/docs/` (11 English, 3 Hinglish) + the concept graph. They are **project-authored** and flagged `verified_official: false`; the UI prints "project-authored, not an official publication" next to every such citation. To add real official material, drop PDFs/txt in `data/raw/` with a `.meta.json` sidecar (`verified_official: true`) and re-ingest.
* **Retrieval:** hybrid — multilingual MiniLM embeddings (`paraphrase-multilingual-MiniLM-L12-v2`, CPU) blended with BM25 — computed in a background thread; **keyword (BM25 + term coverage) fallback** when embeddings are disabled/unavailable.
* **Answering:** concept-alias lookup (English/Hinglish/Hindi terms) gives the curated plain-language definition in the learner's language; retrieved chunks add citations; the LLM (English only) may rephrase within the retrieved context; otherwise an extractive answer is returned. Language is auto-detected ("Volatility kya hoti hai?" → Hinglish).
* **No evidence → no answer:** below the score threshold the reply is exactly *"I don't have enough verified information to establish that."* with no citations. Regulatory-sounding sentences are rewritten unless built from cited text.

## Voice (`ai/voice/`)

* **TTS:** Piper (`en_US-lessac-low`, `hi_IN-pratham-medium`, ≈ 60 MB each). Hindi voice reads Devanagari; Hinglish (Roman) is read by the English voice (intelligible, not native-accented).
* **STT:** faster-whisper `base` int8 on CPU, model downloaded into `data/models` on first use (a symlink-free download, because Windows without developer mode forbids HF's symlinks). Verified round trip: TTS → STT returned the exact sentence in ≈ 0.4 s warm.
* **Isolation:** both run in a separate worker process (`ai/voice/worker.py`). Reason: on this machine importing `onnxruntime` *after* scikit-learn segfaults the interpreter — an uncatchable crash that would take down the API. In the worker `onnxruntime` is imported first and sklearn never is. The worker is started lazily, restarted on failure, killed on timeout.
* **Fallbacks:** if the local engine is missing or fails, the browser Web Speech API is used (read-aloud and dictation); if that is missing too, the UI says so and the learner types. Microphone permission denied → typed input.

## Components and graceful degradation

| If this is missing… | …the product does this |
|---|---|
| Ollama / model | templates only; no coach note; extractive Q&A |
| embeddings model | BM25 keyword retrieval |
| Piper / Whisper | browser speech → plain text |
| trained classifiers | rule signals + choice signals |
| network | nothing changes — all assets and models are local |
| `ARTH_LOW_RESOURCE=1` | LLM, embeddings and STT are all disabled |
