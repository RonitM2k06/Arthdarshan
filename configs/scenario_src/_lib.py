"""Authoring helpers. Write each string once with its translations; compile to canonical JSON + i18n overlay.

    L("English", "Hinglish", "हिन्दी")  ->  English is canonical; others become i18n overlays keyed by dotted path.
"""
from __future__ import annotations

from typing import Any


class L:
    __slots__ = ("en", "hing", "hi")

    def __init__(self, en: str, hing: str | None = None, hi: str | None = None):
        self.en, self.hing, self.hi = en, hing, hi


def _walk(node: Any, path: list[str], overlay: dict[str, dict[str, str]]) -> Any:
    if isinstance(node, L):
        key = ".".join(path)
        if node.hing:
            overlay["hinglish"][key] = node.hing
        if node.hi:
            overlay["hi"][key] = node.hi
        return node.en
    if isinstance(node, dict):
        return {k: _walk(v, path + [str(k)], overlay) for k, v in node.items()}
    if isinstance(node, list):
        out = []
        for i, item in enumerate(node):
            seg = str(item["id"]) if isinstance(item, dict) and isinstance(item.get("id"), str) else str(i)
            out.append(_walk(item, path + [seg], overlay))
        return out
    return node


def compile_scenario(src: dict[str, Any]) -> dict[str, Any]:
    overlay: dict[str, dict[str, str]] = {"hinglish": {}, "hi": {}}
    data = _walk(src, [], overlay)
    data["i18n"] = {k: v for k, v in overlay.items() if v}
    return data


# --- constructors -----------------------------------------------------------------------------------
def A(id: str, label: Any, quality: str, next: str, consequence: Any, *, simple: Any = None, **kw: Any) -> dict:
    d: dict[str, Any] = {"id": id, "label": label, "quality": quality, "next": next, "consequence": consequence}
    if simple is not None:
        d["simple_label"] = simple
    d.update(kw)
    return d


def E(id: str, label: Any, text: Any, kind: str, why: Any = None, risk: str | None = None) -> dict:
    d: dict[str, Any] = {"id": id, "label": label, "text": text, "kind": kind}
    if why is not None:
        d["why"] = why
    if risk:
        d["risk_factor"] = risk
    return d


def P(type: str, text: Any, countdown: int | None = None, intensity: int = 2) -> dict:
    d: dict[str, Any] = {"type": type, "text": text, "intensity": intensity}
    if countdown:
        d["countdown_seconds"] = countdown
    return d


def CH(type: str, sender: str | None, messages: list[Any]) -> dict:
    return {"type": type, "sender": sender, "messages": messages}


def ST(id: str, title: Any, narrative: Any, *, channel: dict | None = None, pressure: list | None = None,
       evidence: list | None = None, actions: list | None = None, reasoning_prompt: Any = None,
       simulation_hint: str | None = None) -> dict:
    d: dict[str, Any] = {"id": id, "title": title, "narrative": narrative, "channel": channel or CH("none", None, []),
                         "pressure": pressure or [], "evidence": evidence or [], "actions": actions or []}
    if reasoning_prompt is not None:
        d["reasoning_prompt"] = reasoning_prompt
    if simulation_hint:
        d["simulation_hint"] = simulation_hint
    return d


def END(id: str, kind: str, headline: Any, summary: Any, narrative: Any = None, loss: int | None = None,
        title: Any = None) -> dict:
    out: dict[str, Any] = {"headline": headline, "summary": summary, "kind": kind}
    if loss is not None:
        out["simulated_loss"] = loss
    return {"id": id, "title": title or headline, "narrative": narrative or summary, "channel": CH("none", None, []),
            "pressure": [], "evidence": [], "actions": [], "terminal": True, "outcome": out}


def scenario(id: str, title: Any, tagline: Any, character: dict, difficulty: int, concept_tags: list[str],
             pressure_tags: list[str], tests: list[str], initial: str, states: list[dict], reflection: dict,
             dimensions: list[str]) -> dict:
    return {
        "id": id, "version": 1, "title": title, "tagline": tagline, "character": character,
        "difficulty": difficulty, "concept_tags": concept_tags, "pressure_tags": pressure_tags,
        "tests_misconceptions": tests, "initial_state": initial, "states": {s["id"]: s for s in states},
        "reflection": reflection, "scoring": {"dimensions": dimensions},
    }
