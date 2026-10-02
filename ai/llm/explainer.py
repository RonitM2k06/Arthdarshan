"""Explanation layer: local LLM when available and valid, otherwise deterministic templates.

Contract: the LLM receives ONLY structured facts computed by the deterministic engine, must answer in JSON,
must not introduce numbers that were not provided, and passes the Safety Gateway. Any failure -> template.
"""
from __future__ import annotations

import json
import logging

from ai.safety.gateway import check_output
from . import client
from .templates import build_explanation

log = logging.getLogger("arth.explain")
LANG_NAME = {"en": "English", "hinglish": "Hinglish (Hindi written in Roman letters, simple words)", "hi": "Hindi (Devanagari, simple words)"}

SYSTEM = (
    "You are the explainer inside ARTHDARSHAN, an educational financial-decision-resilience simulator. "
    "RULES: Use ONLY the facts in the user message. Never recommend, rank or name any product, stock, fund, broker or app. "
    "Never predict prices or returns. Never state regulatory rules. Never ask for OTP, PIN, password, Aadhaar, PAN or card details. "
    "Be warm, brief and non-judgemental: never call the learner careless, foolish or irrational. "
    "Write 2 to 4 short sentences in the requested language. Do not invent numbers. "
    'Reply as JSON: {"explanation": "<text>"}'
)


def explain_decision(facts: dict, lang: str = "en") -> tuple[str, str]:
    """Returns (text, source) where source is 'llm' or 'template'."""
    template_text = build_explanation(facts, lang)
    if not client.status()["available"]:
        return template_text, "template"
    compact = {k: facts[k] for k in ("scenario_title", "state_title", "action_label", "quality", "pressure_types", "noticed", "missed",
                                     "behaviours", "misconceptions", "red_flag_total", "confidence") if k in facts}
    blob = json.dumps(compact, ensure_ascii=False)
    prompt = (f"Language: {LANG_NAME.get(lang, 'English')}.\nFacts (computed by the simulator, authoritative):\n{blob}\n"
              "Write a supportive explanation of the learner's decision using these facts only.")
    out = client.parse_json(client.generate(prompt, SYSTEM, json_mode=True, max_tokens=200))
    text = (out or {}).get("explanation") if out else None
    if not isinstance(text, str) or not (20 <= len(text) <= 700):
        return template_text, "template"
    if not client.numbers_grounded(text, blob):
        log.info("LLM explanation rejected: ungrounded numbers")
        return template_text, "template"
    safe = check_output(text, lang)
    if not safe.allowed:
        log.info("LLM explanation rejected by safety gateway: %s", safe.categories)
        return template_text, "template"
    return text, "llm"


def answer_question(question: str, context: str, lang: str = "en") -> str | None:
    """Short grounded answer from supplied context (used by Q&A). None when the LLM is unavailable/invalid."""
    if not client.status()["available"]:
        return None
    prompt = (f"Language: {LANG_NAME.get(lang, 'English')}.\nContext (verified educational material):\n{context}\n\nQuestion: {question}\n"
              "Answer in at most 4 short sentences using ONLY the context. If the context does not answer it, reply exactly: "
              "\"I don't have enough verified information to establish that.\"")
    out = client.parse_json(client.generate(prompt, SYSTEM, json_mode=True, max_tokens=220))
    text = (out or {}).get("explanation") if out else None
    if not isinstance(text, str) or not text.strip() or len(text) > 800:
        return None
    if not client.numbers_grounded(text, context + question):
        return None
    safe = check_output(text, lang, cited=True)
    return text if safe.allowed else None
