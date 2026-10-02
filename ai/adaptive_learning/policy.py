"""Transparent adaptive training policy.

weakness (low fingerprint dimension / unresolved misconception)
   -> training tags (pressure types, concepts)
   -> candidate scenarios scored by tag overlap, novelty and difficulty fit
   -> top choice with a human-readable rationale.

Nothing here is a black box: every score term is listed in `Recommendation.reasons`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from ai.scenario_engine.schema import DIMENSIONS, Scenario

DIM_NAMES = {
    "concept_knowledge": "Financial Concept Knowledge", "risk_recognition": "Risk Recognition",
    "evidence_verification": "Evidence Verification", "scam_awareness": "Scam Awareness",
    "fomo_resistance": "FOMO Resistance", "herd_resistance": "Herd Behaviour Resistance",
    "emotional_discipline": "Emotional Discipline", "independent_reasoning": "Independent Reasoning",
    "uncertainty_awareness": "Uncertainty Awareness", "terminology": "Financial Terminology Understanding",
}

# weakness -> what the next training should contain
DIM_TRAINING = {
    "fomo_resistance": {"pressure": {"urgency", "scarcity", "countdown", "fomo", "peer_pressure"}, "concepts": {"fomo"}, "sims": ["scam_loss"]},
    "herd_resistance": {"pressure": {"social_proof", "peer_pressure"}, "concepts": {"social_proof"}, "sims": []},
    "emotional_discipline": {"pressure": {"fear", "loss_recovery", "greed"}, "concepts": {"volatility"}, "sims": ["volatility"]},
    "evidence_verification": {"pressure": {"authority"}, "concepts": {"verification", "financial_disclosures"}, "sims": []},
    "scam_awareness": {"pressure": {"authority", "urgency"}, "concepts": {"fraud_red_flags"}, "sims": ["scam_loss"]},
    "risk_recognition": {"pressure": set(), "concepts": {"risk", "diversification", "concentration_risk"}, "sims": ["concentration", "diversification"]},
    "concept_knowledge": {"pressure": set(), "concepts": {"fees", "diversification", "mutual_fund"}, "sims": ["fee_erosion", "compounding"]},
    "independent_reasoning": {"pressure": {"social_proof", "authority"}, "concepts": {"verification", "social_proof"}, "sims": []},
    "uncertainty_awareness": {"pressure": {"fear"}, "concepts": {"volatility", "risk"}, "sims": ["volatility"]},
    "terminology": {"pressure": set(), "concepts": {"financial_disclosures", "nav", "bond", "mutual_fund"}, "sims": []},
}
# extra training that is *not* a scenario
DIM_EXTRA = {
    "terminology": [("lesson", "terminology_micro_lessons", "Micro-lessons and a voice explanation of key terms")],
    "concept_knowledge": [("simulation", "fee_erosion", "Fee erosion simulation")],
}
MISC_SIMS = {"M012": "fee_erosion", "M004": "diversification", "M009": "scam_loss", "M010": "scam_loss", "M003": "compounding"}

STRONG = 70.0
WEAK = 60.0


@dataclass
class Weakness:
    kind: str            # dimension | misconception | unmeasured
    key: str
    label: str
    severity: float      # 0..1
    detail: str


@dataclass
class UserState:
    dimension_scores: dict[str, tuple[float, int]] = field(default_factory=dict)  # dim -> (score, n_obs)
    concept_mastery: dict[str, float] = field(default_factory=dict)
    misconceptions: dict[str, dict] = field(default_factory=dict)  # id -> {detections, status, clean_streak}
    completed: list[tuple[str, str]] = field(default_factory=list)  # (scenario_id, outcome) oldest->newest


@dataclass
class Recommendation:
    kind: str                  # scenario | simulation | lesson
    id: str
    title: str
    difficulty: int | None
    score: float
    weakness: str | None
    rationale: str
    reasons: list[str] = field(default_factory=list)
    predicted_success: float | None = None
    mastery_estimate: float | None = None

    def to_dict(self) -> dict:
        return {"kind": self.kind, "id": self.id, "title": self.title, "difficulty": self.difficulty,
                "score": round(self.score, 2), "weakness": self.weakness, "rationale": self.rationale,
                "reasons": self.reasons, "predicted_success": self.predicted_success,
                "mastery_estimate": self.mastery_estimate}


def find_weaknesses(state: UserState) -> list[Weakness]:
    out: list[Weakness] = []
    for dim in DIMENSIONS:
        score, n = state.dimension_scores.get(dim, (50.0, 0))
        if n == 0:
            out.append(Weakness("unmeasured", dim, DIM_NAMES[dim], 0.25, "not measured yet"))
        elif score < WEAK:
            sev = min(1.0, (WEAK - score) / WEAK + 0.35)
            out.append(Weakness("dimension", dim, DIM_NAMES[dim], sev, f"{DIM_NAMES[dim]} {score:.0f}/100 from {n} observation(s)"))
    for mid, info in state.misconceptions.items():
        if info.get("status") == "resolved":
            continue
        if info.get("detections", 0) > 0:
            sev = min(1.0, 0.55 + 0.1 * info["detections"] - 0.1 * info.get("clean_streak", 0))
            out.append(Weakness("misconception", mid, mid, max(sev, 0.3), f"{mid} detected {info['detections']} time(s)"))
    return sorted(out, key=lambda w: -w.severity)


def target_difficulty(state: UserState) -> tuple[int, float]:
    """Pick difficulty from overall readiness (mean of measured dimensions + concept mastery)."""
    scores = [s for s, n in state.dimension_scores.values() if n > 0]
    mast = list(state.concept_mastery.values())
    parts = []
    if scores:
        parts.append(sum(scores) / len(scores) / 100)
    if mast:
        parts.append(sum(mast) / len(mast))
    ready = sum(parts) / len(parts) if parts else 0.2
    d = 1 if ready < 0.45 else 2 if ready < 0.68 else 3
    return d, ready


def heuristic_success(ready: float, difficulty: int) -> float:
    return max(0.05, min(0.95, ready + 0.25 - 0.2 * difficulty))


def rank_scenarios(state: UserState, scenarios: dict[str, Scenario], titles: dict[str, str] | None = None,
                   success_fn: Callable[[float, int, "Scenario"], float] | None = None,
                   hero: str = "guaranteed_opportunity") -> list[Recommendation]:
    weak = find_weaknesses(state)
    target, ready = target_difficulty(state)
    played = [s for s, _ in state.completed]
    last_outcome = {s: o for s, o in state.completed}
    recs: list[Recommendation] = []
    for sid, sc in scenarios.items():
        reasons: list[str] = []
        score = 0.0
        best_weak: Weakness | None = None
        best_w_score = 0.0
        for w in weak:
            overlap = 0.0
            if w.kind in ("dimension", "unmeasured"):
                t = DIM_TRAINING[w.key]
                p_hit = sorted(set(sc.pressure_tags) & t["pressure"])
                c_hit = sorted(set(sc.concept_tags) & t["concepts"])
                focus = w.key in sc.scoring.dimensions
                primary = bool(sc.scoring.dimensions) and sc.scoring.dimensions[0] == w.key
                overlap = 0.5 * min(1, len(p_hit) / 2) + 0.3 * min(1, len(c_hit)) + (0.4 if focus else 0) + (0.25 if primary else 0)
                if overlap > 0:
                    bits = []
                    if p_hit:
                        bits.append("pressure: " + ", ".join(p_hit))
                    if c_hit:
                        bits.append("concepts: " + ", ".join(c_hit))
                    if focus:
                        bits.append("trains this dimension directly")
                    why = f"{w.detail}; scenario has {'; '.join(bits)}"
                else:
                    why = ""
            else:
                hit = w.key in sc.tests_misconceptions
                primary_m = hit and sc.tests_misconceptions[0] == w.key
                overlap = (0.9 + (0.3 if primary_m else 0)) if hit else 0
                why = (f"{w.key} has been detected and this scenario tests it" + (" as its main focus" if primary_m else "")) if hit else ""
            contrib = w.severity * overlap
            if contrib > 0:
                score += contrib
                reasons.append(f"+{contrib:.2f} {why}")
            if contrib > best_w_score:
                best_w_score, best_weak = contrib, w
        # novelty / repetition
        if sid not in played:
            score += 0.35
            reasons.append("+0.35 not played yet")
        else:
            rep = played.count(sid)
            score -= 0.3 * rep
            reasons.append(f"-{0.3 * rep:.2f} already played {rep}x")
            if last_outcome.get(sid) == "safe":
                score -= 0.25
                reasons.append("-0.25 last attempt ended safely")
        # difficulty fit (zone of proximal development)
        p_succ = success_fn(ready, sc.difficulty, sc) if success_fn else heuristic_success(ready, sc.difficulty)
        zpd = -abs(p_succ - 0.65) * 1.2
        score += zpd
        reasons.append(f"{zpd:+.2f} difficulty {sc.difficulty} vs target {target} (predicted success {p_succ:.2f}, ideal ≈0.65)")
        if not state.completed and sid == hero:
            score += 2.0
            reasons.append("+2.00 recommended first experience")
        title = (titles or {}).get(sid, sc.title)
        if best_weak is not None:
            rationale = f"Because {best_weak.detail}. Difficulty {sc.difficulty} fits your current readiness ({ready:.0%})."
        elif not state.completed:
            rationale = "A good first experience: one scenario covering the most common scam pattern."
        else:
            rationale = f"Broadens practice with a scenario you haven't tried (difficulty {sc.difficulty})."
        recs.append(Recommendation("scenario", sid, title, sc.difficulty, score, best_weak.key if best_weak else None, rationale,
                                   reasons, round(p_succ, 2), round(ready, 2)))
    return sorted(recs, key=lambda r: -r.score)


def recommend_other(state: UserState) -> list[Recommendation]:
    out: list[Recommendation] = []
    seen: set[str] = set()
    for w in find_weaknesses(state):
        if w.kind == "dimension" and w.key in DIM_TRAINING:
            for sim in DIM_TRAINING[w.key]["sims"][:1]:
                if sim not in seen:
                    out.append(Recommendation("simulation", sim, sim.replace("_", " ").title(), None, w.severity, w.key,
                                              f"Because {w.detail}, try the {sim.replace('_', ' ')} simulation (illustrative, no real money).", []))
                    seen.add(sim)
            for kind, tid, title in DIM_EXTRA.get(w.key, []):
                if tid not in seen:
                    out.append(Recommendation(kind, tid, title, None, w.severity, w.key, f"Because {w.detail}: {title}.", []))
                    seen.add(tid)
        if w.kind == "misconception" and w.key in MISC_SIMS and MISC_SIMS[w.key] not in seen:
            sim = MISC_SIMS[w.key]
            out.append(Recommendation("simulation", sim, sim.replace("_", " ").title(), None, w.severity, w.key,
                                      f"{w.key} has been detected; this simulation shows the consequence concretely.", []))
            seen.add(sim)
    return sorted(out, key=lambda r: -r.score)[:4]
