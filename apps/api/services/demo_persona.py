"""A SCRIPTED sample learner for demos. Every decision below is pushed through the real engine, safety layer, analysers and
scoring exactly like a human's; only the *choices* are scripted. The profile is labelled as scripted everywhere it shows."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from apps.api.deps import hash_token, new_token
from apps.api.schemas.core import DecisionIn
from apps.api.services import sessions
from database import models as m

HERO_FLAGS = ["e_auth", "e_guar", "e_scarce", "e_urgent", "e_stranger", "e_group", "e_missing"]

# (scenario, [(state, action, reasoning, confidence, latency_ms, noticed)])
RUNS = [
    ("guaranteed_opportunity", [
        ("s1_message", "invest", "My friend invested so it is probably legit and it is guaranteed", 5, 2200, ["e_guar"]),
        ("s2_fee", "pay_fee", "I have already paid so I must pay once more to recover it", 4, 3100, []),
        ("s7_spiral", "stop_report", "Now I see the pattern, I will stop and report it", 3, 9000, ["sp_new", "sp_tax"])]),
    ("urgent_decision", [("u1_timer", "join_now", "Only a few slots left so I must join right now, I do not want to miss out", 4, 1800, [])]),
    ("guaranteed_opportunity", [
        ("s1_message", "investigate", "Nobody can guarantee 30% so I will verify the registration on the official website first", 3, 11000, HERO_FLAGS),
        ("s6_investigation", "report_leave", "No registration found, so I will leave and report it", 4, 9000, ["i_dir", "i_guar", "i_acct", "i_del"])]),
    ("urgent_decision", [
        ("u1_timer", "pause", "The timer is just pressure, I will pause and think", 3, 8000, ["p_timer", "p_count", "p_friend", "p_entity"]),
        ("u2_slots", "hold", "Slots shrinking when I hesitate is scripted, I will not decide on a clock", 4, 7000, ["s_drop", "s_shot", "s_same"]),
        ("u3_final", "let_go_check", "Missing an unverified offer costs nothing, I will check it calmly later", 4, 6500, ["f_regret", "f_insult"])]),
    ("hidden_fee", [
        ("f1_brochure", "ask_charges", "I want every charge in rupees before deciding", 3, 9000, ["fb_head", "fb_admin", "fb_gift"]),
        ("f2_charges", "calc_net", "A yearly fee compounds, so I will compare the net amounts", 4, 12000, ["c_year", "c_entry", "c_exit"]),
        ("f3_compare", "ask_docs", "I will read the key facts document and decide only when I can explain it", 3, 10000, ["g_exit"])]),
]


def build(db: Session, lang: str = "en") -> tuple[str, m.User]:
    token = new_token()
    user = m.User(public_id=str(uuid.uuid4()), display_name="Rahul (scripted demo persona)", token_hash=hash_token(token), language=lang, simple_mode=False, is_demo=True)
    db.add(user)
    db.commit()
    for scenario_id, steps in RUNS:
        sess = sessions.start_session(db, user, scenario_id, lang)
        for state, action, reasoning, conf, latency, noticed in steps:
            sessions.decide(db, user, DecisionIn(session_id=sess["session_id"], state_key=state, action_id=action, reasoning=reasoning, confidence=conf,
                                                 latency_ms=latency, evidence_noticed=noticed), lang)
    return token, user
