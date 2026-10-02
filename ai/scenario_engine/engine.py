"""Deterministic scenario state machine.

The engine is a set of pure functions. It never calls an LLM, never uses unseeded randomness and
never mutates the scenario. Scenario truth (transitions, consequences, evidence) lives only here.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .schema import DIMENSIONS, Scenario, State

# --- sensitive-request lint: scenarios must never ask the learner for credentials ---------------
_FORBIDDEN_REQUEST = re.compile(
    r"(share|send|enter|tell|give|type|provide)\s+(me\s+|us\s+)?(your\s+|the\s+)?"
    r"(otp|upi\s*pin|atm\s*pin|cvv|card\s*number|password|aadhaar|aadhar|pan\s*(number|card))",
    re.IGNORECASE)
_ADVICE = re.compile(r"\b(you should (buy|sell|invest in)|we recommend (buying|investing)|best (stock|mutual fund)|"
                     r"will (rise|double|go up) (tomorrow|next))\b", re.IGNORECASE)


class ScenarioError(Exception):
    pass


class InvalidAction(ScenarioError):
    pass


class InvalidState(ScenarioError):
    pass


# --------------------------------------------------------------------------------------------------
# Loading / validation
# --------------------------------------------------------------------------------------------------
def load_scenario(data: dict[str, Any]) -> Scenario:
    return Scenario.model_validate(data)


def load_scenarios_from_dir(path: str | Path) -> list[Scenario]:
    out: list[Scenario] = []
    for p in sorted(Path(path).glob("*.json")):
        out.append(load_scenario(json.loads(p.read_text(encoding="utf-8"))))
    return out


def content_hash(sc: Scenario) -> str:
    return hashlib.sha256(json.dumps(sc.model_dump(), sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _all_text(sc: Scenario) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for sid, st in sc.states.items():
        items += [(f"{sid}.narrative", st.narrative)]
        items += [(f"{sid}.msg", m) for m in st.channel.messages]
        items += [(f"{sid}.pressure", p.text) for p in st.pressure]
        items += [(f"{sid}.evidence.{e.id}", e.text) for e in st.evidence]
        items += [(f"{sid}.action.{a.id}", a.label + " " + a.consequence) for a in st.actions]
    return items


def validate_scenario(sc: Scenario, known_concepts: set[str] | None = None,
                      known_misconceptions: set[str] | None = None) -> list[str]:
    """Return a list of human-readable problems (empty list == valid)."""
    errs: list[str] = []
    if sc.initial_state not in sc.states:
        errs.append(f"initial_state {sc.initial_state!r} is not a state")
    for key, st in sc.states.items():
        if key != st.id:
            errs.append(f"state key {key!r} != state.id {st.id!r}")
        ids = [a.id for a in st.actions]
        if len(ids) != len(set(ids)):
            errs.append(f"{key}: duplicate action ids")
        eids = [e.id for e in st.evidence]
        if len(eids) != len(set(eids)):
            errs.append(f"{key}: duplicate evidence ids")
        if st.terminal:
            if st.actions:
                errs.append(f"{key}: terminal state must not have actions")
            if st.outcome is None:
                errs.append(f"{key}: terminal state needs an outcome")
        else:
            if len(st.actions) < 2:
                errs.append(f"{key}: non-terminal state needs >= 2 actions")
            if not any(a.quality == "safe" for a in st.actions):
                errs.append(f"{key}: no action with quality 'safe' (every decision needs a defensible path)")
        for a in st.actions:
            if a.next not in sc.states:
                errs.append(f"{key}.{a.id}: next state {a.next!r} does not exist")
            if known_misconceptions is not None:
                for m in a.misconception_signals:
                    if m not in known_misconceptions:
                        errs.append(f"{key}.{a.id}: unknown misconception {m}")
        for e in st.evidence:
            if e.kind == "red_flag" and not e.why:
                errs.append(f"{key}.{e.id}: red_flag evidence needs a 'why' explanation")
        for p in st.pressure:
            if p.type == "countdown" and not p.countdown_seconds:
                errs.append(f"{key}: countdown pressure needs countdown_seconds")
    # reachability from initial state
    if sc.initial_state in sc.states:
        seen: set[str] = set()
        stack = [sc.initial_state]
        while stack:
            cur = stack.pop()
            if cur in seen or cur not in sc.states:
                continue
            seen.add(cur)
            stack += [a.next for a in sc.states[cur].actions]
        for key in sc.states:
            if key not in seen:
                errs.append(f"state {key!r} unreachable from initial state")
    # every state can reach a terminal state (no dead loops)
    can_end = {k for k, s in sc.states.items() if s.terminal}
    changed = True
    while changed:
        changed = False
        for k, s in sc.states.items():
            if k not in can_end and any(a.next in can_end for a in s.actions):
                can_end.add(k)
                changed = True
    for k in sc.states:
        if k not in can_end:
            errs.append(f"state {k!r} cannot reach any terminal state")
    # tags
    if known_concepts is not None:
        for c in sc.concept_tags + [sc.reflection.micro_lesson.concept_id]:
            if c not in known_concepts:
                errs.append(f"unknown concept {c!r}")
    for d in sc.scoring.dimensions:
        if d not in DIMENSIONS:
            errs.append(f"unknown scoring dimension {d}")
    if known_misconceptions is not None:
        for m in sc.tests_misconceptions:
            if m not in known_misconceptions:
                errs.append(f"tests_misconceptions: unknown {m}")
    # safety lint
    for where, text in _all_text(sc):
        if _FORBIDDEN_REQUEST.search(text):
            errs.append(f"{where}: scenario text requests sensitive data")
        if _ADVICE.search(text):
            errs.append(f"{where}: scenario text reads like investment advice")
    if sc.disclaimer.upper().count("NO REAL MONEY") == 0:
        errs.append("disclaimer must state NO REAL MONEY")
    return errs


def assert_valid(sc: Scenario, **kw: Any) -> None:
    errs = validate_scenario(sc, **kw)
    if errs:
        raise ScenarioError("; ".join(errs))


# --------------------------------------------------------------------------------------------------
# Localisation overlay: i18n[lang] maps dotted paths -> replacement text.
# list items are addressed by their `id` (or integer index), e.g. "states.s1.actions.invest.label"
# --------------------------------------------------------------------------------------------------
def _resolve_and_set(node: Any, parts: list[str], value: str) -> bool:
    if not parts:
        return False
    head, rest = parts[0], parts[1:]
    if isinstance(node, dict):
        if head not in node:
            return False
        if not rest:
            node[head] = value
            return True
        return _resolve_and_set(node[head], rest, value)
    if isinstance(node, list):
        target = None
        if head.isdigit() and int(head) < len(node):
            idx = int(head)
            if not rest:
                node[idx] = value
                return True
            target = node[idx]
        else:
            for item in node:
                if isinstance(item, dict) and item.get("id") == head:
                    target = item
                    break
        if target is None:
            return False
        return _resolve_and_set(target, rest, value) if rest else False
    return False


def localize(sc: Scenario, lang: str) -> Scenario:
    """Return a copy with text replaced by the overlay for `lang`. Hindi is layered on top of Hinglish, so scenarios that have
    no Hindi translation yet show Roman-script Hinglish (readable by Hindi speakers) rather than English. Unknown -> English."""
    layers = [sc.i18n[k] for k in (("hinglish", "hi") if lang == "hi" else (lang,)) if sc.i18n.get(k)]
    if not layers:
        return sc
    data = sc.model_dump()
    for overlay in layers:
        for path, text in overlay.items():
            _resolve_and_set(data, path.split("."), text)
    return Scenario.model_validate(data)


# --------------------------------------------------------------------------------------------------
# Execution
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class EvidenceRecall:
    red_flags: list[str]
    noticed_red_flags: list[str]
    missed_red_flags: list[str]
    false_alarms: list[str]  # neutral/reassuring items flagged as suspicious (not penalised)
    recall: float | None  # None when the state has no red flags


@dataclass(frozen=True)
class StepResult:
    state_key: str
    action_id: str
    quality: str
    next_state_key: str
    consequence: str
    terminal: bool
    evidence: EvidenceRecall
    misconception_signals: list[str] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    verification: bool | None = None
    requests_evidence: bool = False
    pressure_types: list[str] = field(default_factory=list)
    countdown_seconds: int | None = None


def get_state(sc: Scenario, state_key: str) -> State:
    try:
        return sc.states[state_key]
    except KeyError as exc:
        raise InvalidState(f"unknown state {state_key!r}") from exc


def evidence_recall(state: State, noticed: list[str]) -> EvidenceRecall:
    valid = {e.id: e for e in state.evidence}
    noticed_set = {n for n in noticed if n in valid}  # ignore unknown ids rather than trusting client
    red = [e.id for e in state.evidence if e.kind == "red_flag"]
    got = [i for i in red if i in noticed_set]
    missed = [i for i in red if i not in noticed_set]
    false_alarms = [i for i in noticed_set if valid[i].kind in ("neutral", "reassuring")]
    return EvidenceRecall(red, got, missed, sorted(false_alarms), (len(got) / len(red)) if red else None)


def step(sc: Scenario, state_key: str, action_id: str, noticed_evidence: list[str] | None = None) -> StepResult:
    state = get_state(sc, state_key)
    if state.terminal:
        raise InvalidAction("scenario already finished")
    action = next((a for a in state.actions if a.id == action_id), None)
    if action is None:
        raise InvalidAction(f"action {action_id!r} not available in state {state_key!r}")
    nxt = get_state(sc, action.next)
    cd = next((p.countdown_seconds for p in state.pressure if p.countdown_seconds), None)
    return StepResult(
        state_key=state_key, action_id=action.id, quality=action.quality, next_state_key=action.next,
        consequence=action.consequence, terminal=nxt.terminal,
        evidence=evidence_recall(state, noticed_evidence or []),
        misconception_signals=list(action.misconception_signals),
        observations=[o.model_dump() for o in action.observations],
        verification=action.verification, requests_evidence=action.requests_evidence,
        pressure_types=[p.type for p in state.pressure], countdown_seconds=cd,
    )


def public_state_view(sc: Scenario, state_key: str, simple: bool = False) -> dict[str, Any]:
    """What the client may see BEFORE deciding. Evidence classification (kind/why) is withheld."""
    st = get_state(sc, state_key)
    view: dict[str, Any] = {
        "id": st.id, "title": st.title, "narrative": st.narrative, "channel": st.channel.model_dump(),
        "pressure": [p.model_dump() for p in st.pressure],
        "evidence": [{"id": e.id, "label": e.label, "text": e.text} for e in st.evidence],
        "actions": [{"id": a.id, "label": (a.simple_label if simple and a.simple_label else a.label)}
                    for a in st.actions],
        "terminal": st.terminal, "reasoning_prompt": st.reasoning_prompt, "simulation_hint": st.simulation_hint,
    }
    if st.terminal and st.outcome:
        view["outcome"] = st.outcome.model_dump()
    return view


def reveal_evidence(state: State) -> list[dict[str, Any]]:
    """Post-decision explanation of each evidence item."""
    return [e.model_dump() for e in state.evidence]


def path_depth(sc: Scenario) -> tuple[int, int]:
    """(shortest, longest-simple-acyclic-bounded) path length to a terminal; used by tests/analytics."""
    from collections import deque
    dist = {sc.initial_state: 0}
    q = deque([sc.initial_state])
    shortest = None
    while q:
        cur = q.popleft()
        st = sc.states[cur]
        if st.terminal:
            shortest = dist[cur] if shortest is None else min(shortest, dist[cur])
            continue
        for a in st.actions:
            if a.next not in dist:
                dist[a.next] = dist[cur] + 1
                q.append(a.next)
    longest = max(dist.values()) if dist else 0
    return shortest or 0, longest


def deep_copy(sc: Scenario) -> Scenario:
    return copy.deepcopy(sc)
