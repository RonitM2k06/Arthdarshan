"""Explanation layer.

DESIGN (revised after testing a 3B local model): everything FACTUAL about a decision (what was noticed, what was missed,
the pattern, the misconception correction) comes from the deterministic engine and templates. A small local LLM cannot be
trusted to restate scenario facts (in testing it once turned "the sender *claims* registration" into "it *lacks*
registration"), so it is limited to an optional, clearly labelled COACH NOTE that reflects on the learner's own words and
suggests one verification habit, with no claims about the scenario. Every LLM output is validated (JSON, length, no invented
numbers, right language, passes the Safety Gateway); any failure -> no note, the product is unchanged.
"""
from __future__ import annotations

import json
import logging
import re

from ai.safety.gateway import check_output
from . import client
from .templates import build_explanation

log = logging.getLogger("arth.explain")
LANG_NAME = {"en": "English", "hinglish": "Hinglish (Hindi written in Roman letters, simple words)", "hi": "Hindi (Devanagari, simple words)"}

SYSTEM = (
    "You are a gentle coach inside ARTHDARSHAN, an educational financial-decision-resilience simulator. "
    "RULES: Never recommend, rank or name any product, stock, fund, broker or app. Never predict prices or returns. "
    "Never state regulatory rules or facts about the scenario. Never ask for OTP, PIN, password, Aadhaar, PAN or card details. "
    "Be warm, brief and non-judgemental: never call the learner careless, foolish or irrational. "
    'Reply as JSON: {"note": "<one or two short sentences>"}'
)

EXAMPLE = {
    "en": "You explained your choice in your own words, and that makes it easier to spot patterns. Before acting on any claim, try asking yourself what you could check without trusting the person who made it.",
    "hinglish": "Aapne apne faisle ko apne shabdon mein samjhaya, isse pattern pakadna aasan hota hai. Kisi bhi daave par kadam uthane se pehle poochho: daava karne wale par bharosa kiye bina main kya check kar sakta hoon?",
    "hi": "आपने अपने फ़ैसले को अपने शब्दों में समझाया, इससे पैटर्न पकड़ना आसान होता है। किसी भी दावे पर कदम उठाने से पहले पूछें: दावा करने वाले पर भरोसा किए बिना मैं क्या जाँच सकता हूँ?",
}
HING_MARKERS = {"hai", "hain", "ka", "ki", "ke", "aap", "aapne", "ko", "mein", "se", "ho", "nahi", "par", "ye", "jo", "karein", "kar", "pehle", "kya"}
_DEV = re.compile(r"[ऀ-ॿ]")


def explain_decision(facts: dict, lang: str = "en") -> tuple[str, str]:
    """Deterministic explanation of a decision. Returns (text, 'template')."""
    return build_explanation(facts, lang), "template"


def _language_ok(text: str, lang: str) -> bool:
    if lang == "hi":
        return len(_DEV.findall(text)) >= 8
    if _DEV.search(text):
        return False
    if lang == "hinglish":
        return len({w.lower() for w in re.findall(r"[A-Za-z]+", text)} & HING_MARKERS) >= 3
    return True


def coach_note(reasoning: str, behaviour_names: list[str], lang: str = "en") -> str | None:
    """Optional LLM reflection on the learner's own reasoning. None when unavailable, too little to interpret, or rejected."""
    reasoning = (reasoning or "").strip()
    if lang != "en":        # measured: the 3B local model's Hindi is unreliable; Hindi/Hinglish stay on curated templates
        return None
    if len(reasoning) < 15 or not client.status()["available"]:
        return None
    prompt = (f"Write ONLY in {LANG_NAME.get(lang, 'English')}.\nStyle example (do not copy): {EXAMPLE.get(lang, EXAMPLE['en'])}\n"
              f"The learner wrote: \"{reasoning[:400]}\"\nPatterns detected by the simulator: {', '.join(behaviour_names[:3]) or 'none'}.\n"
              "Write one or two short sentences that acknowledge something specific in the learner's own words and suggest one habit of checking a claim "
              "independently. Make no claims about the scenario's facts. Do not mention products or what to invest in.")
    out = client.parse_json(client.generate(prompt, SYSTEM, json_mode=True, max_tokens=120, timeout=12))
    text = (out or {}).get("note") if out else None
    if not isinstance(text, str):
        return None
    text = text.strip()
    if not (20 <= len(text) <= 360):
        return None
    if not client.numbers_grounded(text, reasoning):
        log.info("coach note rejected: invented numbers")
        return None
    if not _language_ok(text, lang):
        log.info("coach note rejected: wrong language")
        return None
    if re.search(r"\b(lacks?|doesn'?t have|does not have|is not registered|is fake|is a scam|is fraudulent|nakli hai|dhokha hai)\b", text, re.I):
        log.info("coach note rejected: makes a factual claim about the scenario")
        return None
    if not check_output(text, lang).allowed:
        log.info("coach note rejected by safety gateway")
        return None
    return text


def answer_question(question: str, context: str, lang: str = "en") -> str | None:
    """Short grounded answer from supplied context (used by Q&A). None when the LLM is unavailable/invalid."""
    if not client.status()["available"]:
        return None
    prompt = (f"Write ONLY in {LANG_NAME.get(lang, 'English')}.\nContext (verified educational material):\n{context}\n\nQuestion: {question}\n"
              "Answer in at most 4 short sentences using ONLY the context. If the context does not answer it, reply exactly: "
              "\"I don't have enough verified information to establish that.\" Never recommend products or predict prices.")
    out = client.parse_json(client.generate(prompt, SYSTEM.replace('{"note": "<one or two short sentences>"}', '{"note": "<answer>"}'), json_mode=True, max_tokens=220))
    text = (out or {}).get("note") if out else None
    if not isinstance(text, str) or not text.strip() or len(text) > 800:
        return None
    if not client.numbers_grounded(text, context + question):
        return None
    if not _language_ok(text, lang):
        return None
    safe = check_output(text, lang, cited=True)
    return text if safe.allowed else None
