# HARDWARE.md — Detected hardware and local model selection

Detected on the development machine (Phase 0, 2026-10-02). Nothing was downloaded to produce this.

## Detected hardware

| Item | Value |
|---|---|
| OS | Windows 11 Home (10.0.26200) |
| CPU | Intel Core i7-14700HX, 20 cores / 28 threads |
| GPU | NVIDIA GeForce RTX 4050 Laptop, **6 GB VRAM**, driver 595.97 |
| RAM | 15.8 GB |
| Disk | C: 149 GB free |
| Python | 3.12.7 |
| Node / npm | v24.16.0 / 11.13.0 |
| Docker | 29.0.1 |
| CUDA toolkit (`nvcc`) | not installed (not needed: PyTorch 2.5.1+cu121 bundles CUDA runtime) |
| Ollama | **not installed** |
| ffmpeg | **not installed** |
| Already installed (Python) | fastapi, uvicorn, SQLAlchemy 2, alembic, pydantic 2, scikit-learn 1.4, sentence-transformers 5.2, torch 2.5.1+cu121, pytest |

## Implications

- 6 GB VRAM and ~16 GB shared RAM (browser, Docker and the web app also need memory) mean only small quantized LLMs are realistic, and only one heavy model should be resident at a time.
- The backend dependencies we need are already installed, so no large downloads are required to run the core product.
- The core simulator (scenario engine, scoring, misconceptions, adaptive learning, simulations) is deterministic/classical-ML and needs **no GPU and no model download**. All LLM, STT and TTS pieces are optional enhancements that degrade gracefully.

## Model plan

| Role | Primary | Fallback (always works) | Approx. memory |
|---|---|---|---|
| LLM (explanations, reasoning analysis) | Qwen2.5-3B-Instruct Q4_K_M via Ollama (GPU), ~2 GB VRAM | Deterministic explanation templates keyed by misconception/concept | ~2.5 GB VRAM |
| LLM (CPU mode) | Qwen2.5-1.5B-Instruct Q4 via Ollama on CPU | Templates | ~1.5 GB RAM |
| Embeddings (RAG) | `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers, already installed; handles Hindi/Hinglish) | TF-IDF / BM25 keyword retrieval | ~0.5 GB, CPU is fine |
| STT | `faster-whisper` `small` int8 (CPU) or `base` for low-resource | Browser Web Speech API, then text input | ~0.5–1 GB |
| TTS | Piper (local, small voices) | Browser `speechSynthesis`, then text only | <0.2 GB |
| ML classifiers | scikit-learn (logistic regression / random forest) on sentence embeddings or TF-IDF | Rule/keyword baseline | negligible |

A 7–8B model would need ~5+ GB VRAM at Q4 and would crowd out embeddings, STT and the browser on this machine, so it is not the default. These choices are recommendations; they are only enabled when the models are actually present.

## Loading policy

- **Lazy loading:** no model is imported or loaded at server start. Each is loaded on first use through a single registry (`ai/llm`, `ai/rag`, voice) and unloaded after an idle timeout.
- **Low-resource mode** (`ARTH_LOW_RESOURCE=1`): disables the LLM and STT, uses keyword retrieval and templates only.
- **Health reporting:** `/api/health` and `/api/models` report which components are actually available. Nothing is claimed as available if it isn't.

## Setup steps still needed for optional components (not yet done)

1. Install Ollama, then `ollama pull qwen2.5:3b-instruct` (~2 GB).
2. Install ffmpeg (for faster-whisper audio decoding) and `pip install faster-whisper piper-tts`.
3. Download the embedding model once (needs internet once, then fully offline).

These will be done in Phases 10–11 and only after confirming disk and bandwidth.
