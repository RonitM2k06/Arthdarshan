"""Mastery estimation: Bayesian Knowledge Tracing (BKT), a transparent, classical model.

A learned success predictor (ml/) can be layered on top; BKT remains the always-available baseline.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BKTParams:
    p_init: float = 0.20    # prior probability the concept is already known
    p_learn: float = 0.15   # chance of learning from one practice opportunity
    p_slip: float = 0.10    # knows it but errs
    p_guess: float = 0.20   # doesn't know it but happens to get it right


DEFAULT = BKTParams()


def update(p_known: float, outcome: str, params: BKTParams = DEFAULT) -> float:
    """Update P(known) after one observation.

    outcome: 'safe' (success), 'unsafe' (failure) or 'mixed' (partial: half-weight success evidence).
    """
    p = min(max(p_known, 0.001), 0.999)
    if outcome == "mixed":
        a = update(p, "safe", params)
        b = update(p, "unsafe", params)
        return 0.5 * a + 0.5 * b
    if outcome == "safe":
        post = p * (1 - params.p_slip) / (p * (1 - params.p_slip) + (1 - p) * params.p_guess)
    elif outcome == "unsafe":
        post = p * params.p_slip / (p * params.p_slip + (1 - p) * (1 - params.p_guess))
    else:
        raise ValueError(f"unknown outcome {outcome!r}")
    return post + (1 - post) * params.p_learn


def mastered(p_known: float, threshold: float = 0.8) -> bool:
    return p_known >= threshold
