import pytest

from ai.misconception import behaviour as bh
from ai.misconception.detector import detect, detect_rules
from ai.misconception.taxonomy import MISCONCEPTION_IDS

POSITIVE = {
    "M001": ["It is guaranteed 30% so it sounds great and I will earn.", "pakka return milega isliye invest karunga"],
    "M002": ["So many members are in the group so it must be legit.", "sab log invest kar rahe hain isliye safe hai"],
    "M003": ["It gave 85% last quarter so it will do the same again.", "pichhle saal ka return dekh kar aage bhi wahi milega"],
    "M004": ["If I diversify and spread it around then I can't lose.", "alag alag jagah lagaunga to risk khatam"],
    "M005": ["The higher return is obviously better so I take it.", "sabse zyada return wala better hai"],
    "M006": ["Only 10 slots left so I must join quickly.", "abhi nahi to mauka haath se chala jayega"],
    "M007": ["It is SEBI registered so it is safe.", "sarkari certificate hai isliye sahi hai"],
    "M008": ["It sounds so professional and technical so it must be credible and genuine.", "bade bade words hain isliye expert sahi hai"],
    "M009": ["It is only a small amount so there is no risk.", "bas thoda sa try karta hoon thoda amount hai safe hai"],
    "M010": ["I have already paid so I need to pay once more to recover it.", "nuksaan wapas paane ke liye aur daalunga"],
    "M011": ["My friend invested and told me so it is probably safe.", "dost ne kaha isliye bharosa hai"],
    "M012": ["The fee is only 2% so it doesn't matter.", "fees se kuch fark nahi padta"],
    "M013": ["We can do the nominee paperwork later when needed.", "nomination baad mein kar lenge zaroori nahi"],
}

NEGATIVE = [
    "It says guaranteed returns which is a red flag.",
    "Nobody can guarantee 30% so I think it is a scam.",
    "Many people joined but that is not proof it is genuine.",
    "I want to verify the registration myself before anything.",
    "The deadline is just a pressure tactic so I will wait.",
    "A friend told me but I will check independently first.",
    "The fee looks small but over time it compounds, so I will compare.",
    "I would walk away.",
    "",
]


@pytest.mark.parametrize("mid,texts", POSITIVE.items())
def test_rule_positive(mid, texts):
    for t in texts:
        ids = {d.id for d in detect_rules(t)}
        assert mid in ids, f"{mid} not detected in {t!r}; got {ids}"


@pytest.mark.parametrize("text", NEGATIVE)
def test_rule_negative(text):
    assert detect_rules(text) == [], [d.id for d in detect_rules(text)]


def test_taxonomy_complete():
    assert MISCONCEPTION_IDS[:12] == [f"M{i:03d}" for i in range(1, 13)]


def test_action_signal_and_merge():
    d = detect("My friend invested so it is probably safe.", action_signals=["M011", "M002"])
    by = {x.id: x for x in d}
    assert "rule" in by["M011"].source and "action" in by["M011"].source
    assert by["M002"].source == "action"
    assert by["M011"].confidence > 0.9


def test_ml_probs_threshold():
    d = detect("", ml_probs={"M001": 0.9, "M002": 0.2})
    assert [x.id for x in d] == ["M001"] and d[0].source == "ml"


def test_behaviour_rules_social_proof():
    hits = {h.label for h in bh.classify_rules("My friend invested, so it is probably legitimate.")}
    assert "friend_reliance" in hits
    hits = {h.label for h in bh.classify_rules("Everyone in the group is investing so it works.")}
    assert "social_proof_reliance" in hits


def test_behaviour_positive_and_skeptic():
    hits = {h.label for h in bh.classify_rules("I would check the official website to verify because nobody can guarantee this.")}
    assert "evidence_seeking" in hits and "independent_reasoning" in hits
    assert "social_proof_reliance" not in {h.label for h in bh.classify_rules("Everyone joined but that is not proof.")}


def test_behaviour_context():
    hits = bh.classify_context("unsafe", ["countdown", "scarcity"], 1500, 0.1, False, False)
    assert any(h.label == "urgency_reaction" for h in hits)
    hits = bh.classify_context("safe", ["countdown"], 20000, 0.8, True, True)
    labels = {h.label for h in hits}
    assert {"deliberate_pause", "evidence_seeking"} <= labels


def test_emotions_and_uncertainty():
    assert "fear" in bh.emotional_indicators("I was scared and panicking")
    assert "fomo" in bh.emotional_indicators("I don't want to miss out")
    assert bh.has_uncertainty_recognition("Nobody can know what happens next")
    assert not bh.has_uncertainty_recognition("It will definitely go up")


def test_explanations_nonjudgemental_all_langs():
    banned = ["stupid", "idiot", "careless", "irrational", "foolish", "dumb", "bevakoof", "moorkh"]
    for label in bh.BEHAVIOURS:
        for lang in ("en", "hinglish", "hi"):
            e = bh.explain(label, lang)["explanation"].lower()
            assert not any(b in e for b in banned)
