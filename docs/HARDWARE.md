# HARDWARE.md — detected hardware and the model choices made

Detected on the development machine (Phase 0, 2026-10-02).

| Item | Value |
|---|---|
| OS | Windows 11 Home (10.0.26200) |
| CPU | Intel Core i7-14700HX, 20 cores / 28 threads |
| GPU | NVIDIA GeForce RTX 4050 Laptop, **6 GB VRAM**, driver 595.97 (PyTorch 2.5.1+cu121; no CUDA toolkit needed) |
| RAM | 15.8 GB |
| Disk | C: 149 GB free (project + models ≈ 3 GB) |
| Python / Node / Docker | 3.12.7 / 24.16 / 29.0.1 (Docker not required by the app) |

## What was chosen and what it costs

| Role | Choice | Footprint | Fallback |
|---|---|---|---|
| LLM | Qwen2.5-3B-Instruct Q4 via Ollama (GPU) | 1.9 GB on disk, ≈ 2–2.5 GB VRAM | none needed — templates |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` (CPU) | ≈ 0.5 GB RAM | BM25 keyword retrieval |
| STT | faster-whisper `base`, int8, CPU | ≈ 150 MB disk, < 1 GB RAM | browser speech → typing |
| TTS | Piper `en_US-lessac-low` + `hi_IN-pratham-medium` | ≈ 126 MB disk, CPU | browser speech → text |
| ML | scikit-learn pipelines | < 5 MB | rules |

A 7–8B model would need ≥ 5 GB VRAM and crowd out the browser, embeddings and speech, so it was not downloaded. The core simulator (engine, scoring, misconceptions, adaptive policy, simulations) needs **no GPU and no model download**.

## Loading policy

* No model is loaded at import time. The LLM is warmed in a background thread after start-up; embeddings are computed in a background thread; STT/TTS load in the isolated voice worker on first use; classifiers load on first decision.
* `ARTH_LOW_RESOURCE=1` (or `python scripts/demo.py --low-resource`) disables LLM, embeddings and STT: the app then needs ≈ 300 MB RAM and still plays every scenario.
* `/api/health`, `/api/models` and Settings report what is *actually* available; nothing is claimed that is not loaded.

## Measured on this machine (indicative)

Cold LLM first call > 25 s (hence the background warm-up); warm coach note ≈ 0.7 s; Piper synthesis ≈ 1.5 s first / < 0.1 s warm for a sentence; Whisper-base transcription of a sentence ≈ 0.4 s warm; full ML training 3 s; API start-up to ready ≈ 10–12 s (embedding model load dominates).
