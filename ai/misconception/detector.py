"""Misconception detection: rules (high precision) + optional trained classifier (recall) + choice signals.

The LLM is never the sole source of truth: it is not consulted here at all.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .taxonomy import BY_ID, MISCONCEPTIONS, SKEPTIC

I = re.IGNORECASE
_SKEPTIC = re.compile(SKEPTIC, I)
_COMPILED = {m["id"]: [re.compile(p, I) for p in m["patterns"]] for m in MISCONCEPTIONS}
_BELIEF = {m["id"]: [re.compile(p, I) for p in m.get("needs_belief", [])] for m in MISCONCEPTIONS}


@dataclass
class Detection:
    id: str
    source: str        # rule | ml | action | quiz | rule+ml ...
    confidence: float
    evidence: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "source": self.source, "confidence": round(self.confidence, 2), "evidence": self.evidence}


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?;])\s+|\bbut\b|\bhowever\b|\blekin\b|\bpar\b|\n+", text, flags=I)
    return [p.strip() for p in parts if p and p.strip()]


def detect_rules(text: str) -> list[Detection]:
    found: dict[str, Detection] = {}
    for sent in _sentences(text or ""):
        if _SKEPTIC.search(sent):
            continue  # "it says guaranteed, which is a red flag" is not the misconception
        for mid, pats in _COMPILED.items():
            if mid in found:
                continue
            for p in pats:
                m = p.search(sent)
                if not m:
                    continue
                belief = _BELIEF[mid]
                if belief and not any(b.search(sent) for b in belief):
                    continue
                found[mid] = Detection(mid, "rule", 0.9, m.group(0)[:80])
                break
    return list(found.values())


def detect(text: str, action_signals: list[str] | None = None, ml_probs: dict[str, float] | None = None,
           ml_threshold: float = 0.5) -> list[Detection]:
    """Combine all sources. Each misconception appears once with the strongest evidence and merged sources."""
    merged: dict[str, Detection] = {}

    def add(d: Detection) -> None:
        cur = merged.get(d.id)
        if cur is None:
            merged[d.id] = d
            return
        srcs = set(cur.source.split("+")) | set(d.source.split("+"))
        cur.source = "+".join(sorted(srcs))
        cur.confidence = min(0.99, max(cur.confidence, d.confidence) + 0.04)
        if not cur.evidence:
            cur.evidence = d.evidence

    for d in detect_rules(text):
        add(d)
    for mid, p in (ml_probs or {}).items():
        if p >= ml_threshold and mid in BY_ID:
            add(Detection(mid, "ml", float(p), ""))
    for mid in action_signals or []:
        if mid in BY_ID:
            add(Detection(mid, "action", 0.8, "choice made"))
    return sorted(merged.values(), key=lambda d: -d.confidence)


def correction(mid: str, lang: str = "en") -> dict:
    m = BY_ID[mid]
    lang = lang if lang in ("en", "hinglish", "hi") else "en"
    return {"id": mid, "name": m["name"], "description": m["description"], "correction": m["correction"][lang],
            "concept": m["concept"]}
