"""Local RAG over the knowledge base. Embeddings are optional: without them retrieval falls back to BM25 keywords.

Every answer carries citations (document title, source, date, chunk index, verified_official flag). If retrieval
support is below threshold the answer is exactly: "I don't have enough verified information to establish that."
Nothing regulatory is generated from model memory.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.llm import explainer
from ai.safety.gateway import check_output
from ai.safety.responses import INSUFFICIENT
from apps.api.config import ROOT, get_settings
from apps.api.services.content import load_concepts
from database import models as m

log = logging.getLogger("arth.rag")
CHUNK_CHARS = 650
STOP = set("a an the is are was were be been of to in on for and or but with what why how does do did can could should would it its this that these those i me my you your we our they their at as by from about into than then so if not no kya hai hain hota hoti hote ka ki ke ko se mein par aur ya to toh ye wo yeh woh kaise kyun kab".split())
_embedder_lock = threading.Lock()
_embedder = {"model": None, "tried": False}
_matrix_cache: dict = {"key": None, "ids": [], "mat": None}


# ---------------------------------------------------------------------------------------------------
# text utilities
# ---------------------------------------------------------------------------------------------------
def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[\wऀ-ॿ₹%]+", text.lower()) if t not in STOP and len(t) > 1]


def detect_language(text: str, preferred: str = "en") -> str:
    if re.search(r"[ऀ-ॿ]", text):
        return "hi"
    markers = {"kya", "hai", "hain", "hota", "hoti", "kaise", "kyun", "mein", "karun", "karein", "samjhao", "batao", "mujhe", "kitna", "wala", "nahi", "aur", "ka", "ki", "ke"}
    words = set(re.findall(r"[a-z]+", text.lower()))
    if len(words & markers) >= 2 or ("kya" in words and len(words) <= 6):
        return "hinglish"
    return preferred if preferred in ("en", "hinglish", "hi") and preferred != "hi" else "en"


def chunk_text(text: str, size: int = CHUNK_CHARS) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) > size:
            chunks.append(cur.strip())
            cur = ""
        if len(p) > size:  # split long paragraph on sentences
            for s in re.split(r"(?<=[.!?])\s+", p):
                if cur and len(cur) + len(s) > size:
                    chunks.append(cur.strip())
                    cur = ""
                cur += s + " "
        else:
            cur += p + "\n\n"
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


def parse_markdown(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    meta: dict = {}
    body = raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end > 0:
            for line in raw[3:end].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = raw[end + 4:].strip()
    return meta, body


# ---------------------------------------------------------------------------------------------------
# embeddings (optional)
# ---------------------------------------------------------------------------------------------------
def get_embedder():
    s = get_settings()
    if not s.enable_embeddings or s.low_resource:
        return None
    with _embedder_lock:
        if _embedder["tried"]:
            return _embedder["model"]
        _embedder["tried"] = True
        try:
            from sentence_transformers import SentenceTransformer
            _embedder["model"] = SentenceTransformer(s.embedding_model, device="cpu")
            log.info("embedding model loaded: %s", s.embedding_model)
        except Exception as exc:  # noqa: BLE001
            log.warning("embeddings unavailable (%s); using keyword retrieval", type(exc).__name__)
            _embedder["model"] = None
        return _embedder["model"]


def embedder_status() -> dict:
    s = get_settings()
    if not s.enable_embeddings or s.low_resource:
        return {"available": False, "reason": "disabled", "model": s.embedding_model}
    return {"available": _embedder["model"] is not None, "loaded": _embedder["model"] is not None, "tried": _embedder["tried"], "model": s.embedding_model}


def reset_embedder() -> None:
    with _embedder_lock:
        _embedder.update(model=None, tried=False)
    _matrix_cache.update(key=None, ids=[], mat=None)


def _embed(texts: list[str]) -> np.ndarray | None:
    model = get_embedder()
    if model is None:
        return None
    return np.asarray(model.encode(texts, normalize_embeddings=True, show_progress_bar=False), dtype=np.float32)


# ---------------------------------------------------------------------------------------------------
# ingestion
# ---------------------------------------------------------------------------------------------------
def _read_raw(path: Path) -> tuple[dict, str] | None:
    meta_path = path.with_suffix(".meta.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    meta.setdefault("title", path.stem)
    meta.setdefault("source", "user-supplied document")
    meta.setdefault("source_type", "other")
    meta.setdefault("verified_official", False)
    if path.suffix.lower() in (".txt", ".md"):
        return meta, path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            text = "\n\n".join((pg.extract_text() or "") for pg in PdfReader(str(path)).pages)
            return meta, text
        except Exception as exc:  # noqa: BLE001
            log.warning("could not read %s: %s", path.name, type(exc).__name__)
    return None


def ingest(db: Session, with_embeddings: bool = True) -> dict:
    kb = Path(get_settings().knowledge_dir)
    files: list[tuple[str, dict, str]] = []
    for p in sorted((kb / "docs").glob("*.md")):
        meta, body = parse_markdown(p)
        files.append((p.stem, meta, body))
    raw = ROOT / "data" / "raw"
    if raw.exists():
        for p in sorted(raw.iterdir()):
            if p.suffix.lower() in (".pdf", ".txt", ".md") and not p.name.endswith(".meta.json"):
                r = _read_raw(p)
                if r:
                    files.append((f"raw_{p.stem}", r[0], r[1]))
    n_docs = n_chunks = 0
    for key, meta, body in files:
        h = hashlib.sha256(body.encode()).hexdigest()
        doc = db.scalar(select(m.KnowledgeDocument).where(m.KnowledgeDocument.doc_key == key))
        vo = str(meta.get("verified_official", "false")).lower() == "true"
        if doc is not None and doc.content_hash == h and not (with_embeddings and get_embedder() and any(c.embedding is None for c in doc.chunks)):
            n_docs += 1
            n_chunks += len(doc.chunks)
            continue
        if doc is None:
            doc = m.KnowledgeDocument(doc_key=key, title=meta.get("title", key), source=meta.get("source", ""), source_type=meta.get("source_type", "other"),
                                      verified_official=vo, published_date=meta.get("date"), language=meta.get("language", "en"), content_hash=h,
                                      doc_metadata={k: v for k, v in meta.items() if k not in ("title", "source", "source_type", "date", "language", "verified_official")})
            db.add(doc)
            db.flush()
        else:
            doc.title, doc.source, doc.source_type = meta.get("title", key), meta.get("source", ""), meta.get("source_type", "other")
            doc.verified_official, doc.published_date, doc.language, doc.content_hash = vo, meta.get("date"), meta.get("language", "en"), h
            for c in list(doc.chunks):
                db.delete(c)
            db.flush()
        parts = chunk_text(body)
        embs = _embed(parts) if with_embeddings else None
        for i, text in enumerate(parts):
            db.add(m.KnowledgeChunk(document_id=doc.id, chunk_index=i, text=text, embedding=None if embs is None else embs[i].tobytes(),
                                    embedding_model=get_settings().embedding_model if embs is not None else None,
                                    chunk_metadata={"chars": len(text), "language": doc.language}))
        n_docs += 1
        n_chunks += len(parts)
    db.commit()
    _matrix_cache.update(key=None)
    return {"documents": n_docs, "chunks": n_chunks, "embeddings": get_embedder() is not None and with_embeddings}


# ---------------------------------------------------------------------------------------------------
# retrieval
# ---------------------------------------------------------------------------------------------------
@dataclass
class Hit:
    chunk_id: int
    doc_key: str
    title: str
    source: str
    date: str | None
    verified_official: bool
    source_type: str
    chunk_index: int
    text: str
    score: float
    method: str
    language: str = "en"

    def citation(self) -> dict:
        return {"title": self.title, "source": self.source, "date": self.date, "doc_key": self.doc_key, "chunk": self.chunk_index,
                "verified_official": self.verified_official, "source_type": self.source_type, "score": round(self.score, 3), "method": self.method}


def _bm25(query_tokens: list[str], docs_tokens: list[list[str]], k1: float = 1.5, b: float = 0.75) -> np.ndarray:
    n = len(docs_tokens)
    if n == 0 or not query_tokens:
        return np.zeros(n)
    avg = sum(len(d) for d in docs_tokens) / n or 1.0
    df: dict[str, int] = {}
    for d in docs_tokens:
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    scores = np.zeros(n)
    for i, d in enumerate(docs_tokens):
        tf: dict[str, int] = {}
        for t in d:
            tf[t] = tf.get(t, 0) + 1
        for q in set(query_tokens):
            if q not in tf:
                continue
            idf = math.log(1 + (n - df[q] + 0.5) / (df[q] + 0.5))
            scores[i] += idf * tf[q] * (k1 + 1) / (tf[q] + k1 * (1 - b + b * len(d) / avg))
    return scores


def _load_chunks(db: Session):
    rows = db.execute(select(m.KnowledgeChunk, m.KnowledgeDocument).join(m.KnowledgeDocument)).all()
    return rows


def retrieve(db: Session, query: str, k: int = 4, lang: str | None = None, use_embeddings: bool = True) -> tuple[list[Hit], str]:
    """Returns (hits sorted by score, method) where method is 'hybrid' or 'keyword'."""
    rows = _load_chunks(db)
    if not rows or not query.strip():
        return [], "keyword"
    qtok = tokenize(query)
    toks = [tokenize(c.text + " " + d.title) for c, d in rows]
    bm = _bm25(qtok, toks)
    bm_norm = bm / bm.max() if bm.max() > 0 else bm
    coverage = np.array([len(set(qtok) & set(t)) / max(len(set(qtok)), 1) for t in toks])
    sims = None
    method = "keyword"
    if use_embeddings and get_embedder() is not None and all(c.embedding is not None for c, _ in rows):
        key = (len(rows), rows[-1][0].id)
        if _matrix_cache["key"] != key:
            _matrix_cache.update(key=key, mat=np.vstack([np.frombuffer(c.embedding, dtype=np.float32) for c, _ in rows]))
        qv = _embed([query])
        if qv is not None:
            sims = _matrix_cache["mat"] @ qv[0]
            method = "hybrid"
    if sims is not None:
        score = 0.7 * np.clip(sims, 0, 1) + 0.3 * bm_norm
    else:
        score = 0.55 * bm_norm + 0.45 * coverage
    order = np.argsort(-score)[:k]
    hits = []
    for i in order:
        c, d = rows[i]
        hits.append(Hit(c.id, d.doc_key, d.title, d.source, d.published_date, d.verified_official, d.source_type, c.chunk_index, c.text,
                        float(score[i]), method, d.language))
    return hits, method


# ---------------------------------------------------------------------------------------------------
# answering
# ---------------------------------------------------------------------------------------------------
THRESH = {"hybrid": 0.40, "keyword": 0.34}


def match_concept(question: str) -> dict | None:
    q = question.lower()
    best, best_len = None, 0
    for c in load_concepts():
        for alias in [c["id"].replace("_", " "), c["name"]["en"].lower()] + [a.lower() for a in c.get("aliases", [])]:
            if len(alias) < 3 or len(alias) <= best_len:
                continue
            ascii_alias = re.fullmatch(r"[a-z0-9 ]+", alias) is not None
            if (re.search(rf"\b{re.escape(alias)}\b", q) if ascii_alias else alias in q):
                best, best_len = c, len(alias)
    return best


def _best_sentences(text: str, question: str, n: int = 2) -> str:
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")) if len(s.strip()) > 25]
    qt = set(tokenize(question))
    scored = sorted(sents, key=lambda s: -len(qt & set(tokenize(s))))
    picked = scored[:n]
    return " ".join(s for s in sents if s in picked)


def answer(db: Session, question: str, lang: str = "en") -> dict:
    """Grounded Q&A. Returns {answer, language, citations, grounded, method, source}."""
    lang = detect_language(question, lang)
    concept = match_concept(question)
    hits, method = retrieve(db, question, k=3, lang=lang)
    good = [h for h in hits if h.score >= THRESH[method]]
    citations: list[dict] = []
    context_parts: list[str] = []
    lines: list[str] = []
    if concept is not None:
        cl = lang if lang in concept["simple"] else "en"
        simple = concept["simple"][cl]
        lines.append(simple)
        context_parts.append(f"[Concept: {concept['name']['en']}] {concept['simple']['en']} {concept['detailed']}")
        citations.append({"title": f"ARTHDARSHAN concept graph — {concept['name']['en']}", "source": "ARTHDARSHAN educational content (project-authored)",
                          "date": None, "doc_key": f"concept:{concept['id']}", "chunk": 0, "verified_official": False,
                          "source_type": "project_authored", "score": 1.0, "method": "concept_match"})
    for h in good:
        context_parts.append(f"[{h.title}] {h.text}")
        citations.append(h.citation())
    if not lines and not good:
        return {"answer": INSUFFICIENT.get(lang, INSUFFICIENT["en"]), "language": lang, "citations": [], "grounded": False, "method": method, "source": "none"}
    ctx = "\n\n".join(context_parts)[:3500]
    llm_text = explainer.answer_question(question, ctx, lang)
    source = "llm"
    if llm_text:
        text = llm_text
    else:
        source = "extractive"
        if good and not (lines and lang != "en" and good[0].language == "en"):
            extra = _best_sentences(good[0].text, question)
            if extra and extra not in lines:
                lines.append(extra)
        elif good and lines:
            pass
        text = " ".join(lines)
    safe = check_output(text, lang, cited=True)
    if not safe.allowed:
        return {"answer": safe.text, "language": lang, "citations": [], "grounded": False, "method": method, "source": "safety_rewrite"}
    return {"answer": text, "language": lang, "citations": citations, "grounded": True, "method": method, "source": source}
