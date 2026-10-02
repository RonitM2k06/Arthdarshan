"""Behavioural pattern classification from a learner's reasoning text and decision context.

Rule layer (this file) is deterministic and explainable; the ML layer (ml_models.py) adds recall when a
trained model exists. Explanations are educational and non-judgemental by construction.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

I = re.IGNORECASE

BEHAVIOURS: dict[str, dict] = {
    "social_proof_reliance": {
        "name": "SOCIAL PROOF RELIANCE", "positive": False, "dimension": "herd_resistance",
        "explain": {
            "en": "Other people's participation is not independent evidence that an opportunity is legitimate. Ask what could be checked without trusting the crowd.",
            "hinglish": "Doosron ka judna is baat ka swatantra saboot nahi ki opportunity asli hai. Poochho ki bheed par bharosa kiye bina kya check ho sakta hai.",
            "hi": "दूसरों का जुड़ना इस बात का स्वतंत्र सबूत नहीं कि अवसर असली है। पूछें कि भीड़ पर भरोसा किए बिना क्या जाँचा जा सकता है।"},
        "patterns": [r"(everyone|everybody|many (people|members)|others|sab\s+log|sabhi|bahut\s+log|group|members|240)[^.!?]{0,60}(in|invest\w*|joined|using|kar\s+rahe|jud|legit|safe|sahi|theek)",
                     r"(so many|lots of)\s+(people|members)", r"(popular|crowd|trending)"],
    },
    "friend_reliance": {
        "name": "RELIANCE ON A PERSONAL RECOMMENDATION", "positive": False, "dimension": "independent_reasoning",
        "explain": {
            "en": "A friend can be sincere and still be wrong or fooled. A personal recommendation is a reason to look closer, not a reason to skip checking.",
            "hinglish": "Dost sachcha hokar bhi galat ya dhokhe mein ho sakta hai. Personal salah ek wajah hai aur dhyan se dekhne ki, check chhodne ki nahi.",
            "hi": "दोस्त सच्चा होकर भी गलत या धोखे में हो सकता है। निजी सलाह और ध्यान से देखने की वजह है, जाँच छोड़ने की नहीं।"},
        "patterns": [r"(my\s+)?(friend|cousin|brother|sister|dost|bhai|neha|rajesh|relative|colleague|vikas|kabir)[^.!?]{0,60}(said|told|invested|in|recommend\w*|bataya|kaha|lagaya|made|earned|trust)",
                     r"(trust|believe)\s+(my\s+)?(friend|cousin|brother|dost|bhai)"],
    },
    "authority_reliance": {
        "name": "AUTHORITY RELIANCE", "positive": False, "dimension": "evidence_verification",
        "explain": {
            "en": "Words like 'registered', 'certified' or 'official' are claims until you verify them with the official source yourself.",
            "hinglish": "'Registered', 'certified' ya 'official' jaise shabd tab tak daave hain jab tak aap khud official source se verify na karo.",
            "hi": "'पंजीकृत', 'प्रमाणित' या 'आधिकारिक' जैसे शब्द तब तक दावे हैं जब तक आप खुद आधिकारिक स्रोत से सत्यापित न करें।"},
        "patterns": [r"(sebi|rbi|registered|certified|certificate|official|approved|government|regulated|expert|professional|fund\s+manager)[^.!?]{0,60}(so|therefore|hence|means|isliye|matlab|must|trust|safe|legit|genuine|sahi)",
                     r"(certificate|registration)\s+(looks?|seems?)\s+(real|genuine|official|fine)"],
    },
    "urgency_reaction": {
        "name": "URGENCY REACTION", "positive": False, "dimension": "fomo_resistance",
        "explain": {
            "en": "A deadline or shrinking slots creates a feeling that you must act now. A real, regulated product does not need a decision in minutes; missing an unverified offer costs nothing.",
            "hinglish": "Deadline ya ghat'te slots ye ehsaas dete hain ki abhi karna zaroori hai. Asli, regulated product ko minutes mein faisla nahi chahiye; unverified offer chhootne se kuch nahi jaata.",
            "hi": "समय-सीमा या घटते स्लॉट यह एहसास देते हैं कि अभी करना ज़रूरी है। असली, विनियमित उत्पाद को मिनटों में फ़ैसला नहीं चाहिए; अनजाँचा प्रस्ताव छूटे तो कुछ नहीं जाता।"},
        "patterns": [r"(miss\s+(out|the)|last\s+chance|limited\s+(time|slots)|slots?\s+(ending|filling|left)|deadline|running\s+out|hurry|quickly|immediately|right\s+now|jaldi|abhi|mauka|chhoot)",
                     r"(don'?t|do\s+not|dont)\s+want\s+to\s+miss"],
    },
    "greed_driven": {
        "name": "RETURN-CHASING", "positive": False, "dimension": "emotional_discipline",
        "explain": {
            "en": "A very high promised return is attractive, which is exactly why it is used as bait. Higher promised returns usually mean higher risk or a false promise.",
            "hinglish": "Bahut ooncha vaada kiya gaya return lubhaavna hota hai, isiliye use chaara banaya jaata hai. Zyada vaada aksar zyada risk ya jhootha vaada hota hai.",
            "hi": "बहुत ऊँचा वादा किया गया रिटर्न लुभावना होता है, इसीलिए उसे चारे की तरह इस्तेमाल किया जाता है। ज़्यादा वादा अक्सर ज़्यादा जोखिम या झूठा वादा होता है।"},
        "patterns": [r"(30\s*%|85\s*%|20\s*%|high\s+returns?|big\s+(profit|returns?)|double|rich|jackpot|zyada\s+(return|munafa|profit)|ooncha\s+return|easy\s+money|amazing\s+returns?)"],
    },
    "fear_panic": {
        "name": "FEAR / PANIC RESPONSE", "positive": False, "dimension": "emotional_discipline",
        "explain": {
            "en": "Fear makes the present feel like it will last forever. Writing down your goal and time horizon before acting turns a reaction into a decision.",
            "hinglish": "Darr aaj ko aisa dikhata hai jaise wo hamesha rahega. Kuch karne se pehle goal aur samay-seema likhne se pratikriya faisla ban jaati hai.",
            "hi": "डर वर्तमान को ऐसा दिखाता है जैसे वह हमेशा रहेगा। कुछ करने से पहले लक्ष्य और समय-सीमा लिखने से प्रतिक्रिया फ़ैसला बन जाती है।"},
        "patterns": [r"\b(panic\w*|scared|afraid|terrified|fear|worried|anxious|stress\w*|can'?t\s+stand|ghabra\w*|darr\w*|dar\s+lag|tension|cannot\s+watch|sell\s+everything|sab\s+bech)\b"],
    },
    "loss_chasing": {
        "name": "LOSS-CHASING / SUNK COST", "positive": False, "dimension": "emotional_discipline",
        "explain": {
            "en": "Money already paid or lost is gone either way. Paying more to 'get it back' is how losses grow.",
            "hinglish": "Jo paisa de diya ya kho diya wo dono taraf gaya hi hai. Wapas paane ke liye aur dene se nuksaan badhta hai.",
            "hi": "जो पैसा दे दिया या खो दिया वह दोनों तरफ़ गया ही है। वापस पाने के लिए और देने से नुकसान बढ़ता है।"},
        "patterns": [r"(recover|win\s+back|make\s+up|get\s+(it|my\s+money|the\s+loss)\s+back|already\s+(paid|lost|put|invested)|come\s+this\s+far|itna\s+aage|wapas\s+(paane|lene|mil)|average\s+down|double\s+down)"],
    },
    "evidence_seeking": {
        "name": "EVIDENCE-SEEKING", "positive": True, "dimension": "evidence_verification",
        "explain": {
            "en": "You looked for evidence before deciding. This is the single most protective habit.",
            "hinglish": "Aapne faisle se pehle saboot dhunda. Ye sabse suraksha dene wali aadat hai.",
            "hi": "आपने फ़ैसले से पहले सबूत ढूँढा। यह सबसे सुरक्षा देने वाली आदत है।"},
        "patterns": [r"\b(verify|verified|verification|check\w*|look\s+(it\s+)?up|search\w*|investigat\w*|research\w*|official\s+(site|website)|registry|independent\w*|proof|evidence|saboot|jaanch\w*|pata\s+karun\w*|confirm\w*)\b"],
    },
    "independent_reasoning": {
        "name": "INDEPENDENT REASONING", "positive": True, "dimension": "independent_reasoning",
        "explain": {
            "en": "You based your decision on reasons you could examine yourself rather than on what others said.",
            "hinglish": "Aapne apna faisla un karanon par liya jinhe aap khud parakh sakte the, doosron ke kehne par nahi.",
            "hi": "आपने अपना फ़ैसला उन कारणों पर लिया जिन्हें आप खुद परख सकते थे, दूसरों के कहने पर नहीं।"},
        "patterns": [r"\b(because|since|therefore|so\s+i|my\s+own|myself|on\s+my\s+own|khud|apne\s+aap|isliye|kyunki)\b[^.!?]{0,80}\b(guarante\w*|evidence|proof|risk|fee|charge|registered|verify|check\w*|unverified|saboot|jaanch\w*)\b"],
    },
    "uncertainty_acknowledgement": {
        "name": "UNCERTAINTY AWARENESS", "positive": True, "dimension": "uncertainty_awareness",
        "explain": {
            "en": "You recognised that the future cannot be known. Accepting uncertainty is part of sound decisions.",
            "hinglish": "Aapne maana ki bhavishya jaana nahi ja sakta. Anishchitta ko maanna sahi faisle ka hissa hai.",
            "hi": "आपने माना कि भविष्य जाना नहीं जा सकता। अनिश्चितता को मानना सही फ़ैसले का हिस्सा है।"},
        "patterns": [r"\b(not\s+sure|can'?t\s+be\s+sure|no\s+one\s+(knows|can)|nobody\s+(knows|can)|uncertain\w*|unknown|depends|might|may\s+not|pata\s+nahi|koi\s+nahi\s+jaanta|anishchit\w*|guarantee\s+nahi|cannot\s+predict|can'?t\s+predict)\b"],
    },
    "deliberate_pause": {
        "name": "DELIBERATE PAUSE", "positive": True, "dimension": "emotional_discipline",
        "explain": {
            "en": "You slowed down under pressure. A pause is what turns a reaction into a decision.",
            "hinglish": "Aapne dabaav mein raftaar dheemi ki. Ruk jaana pratikriya ko faisle mein badalta hai.",
            "hi": "आपने दबाव में रफ़्तार धीमी की। रुकना प्रतिक्रिया को फ़ैसले में बदलता है।"},
        "patterns": [r"\b(pause|wait\w*|slow\s+down|take\s+(my\s+)?time|think\s+(about|first)|sleep\s+on|calm\w*|ruk\w*|sochna|soch\s+kar|dheere|shaant|step\s+back|breathe)\b"],
    },
    "overconfidence": {
        "name": "CERTAINTY ABOUT THE UNKNOWABLE", "positive": False, "dimension": "uncertainty_awareness",
        "explain": {
            "en": "Strong certainty about future outcomes is a signal to double-check. No one can reliably know them.",
            "hinglish": "Aage ke nateejon ke baare mein pakka vishwas dobara check karne ka sanket hai. Koi unhe bharosemand tareeke se nahi jaanta.",
            "hi": "भविष्य के नतीजों पर पक्का विश्वास दोबारा जाँचने का संकेत है। कोई उन्हें भरोसेमंद तरीके से नहीं जानता।"},
        "patterns": [r"\b(definitely|certainly|surely|for\s+sure|100\s*%\s*sure|no\s+doubt|can'?t\s+fail|bound\s+to|pakka|zaroor\s+(badhega|chalega)|i\s+am\s+sure\s+it\s+will|i'?m\s+sure\s+it\s+will)\b"],
    },
}

EMOTION_PATTERNS = {
    "fear": r"\b(panic\w*|scared|afraid|terrified|fear|worried|anxious|stress\w*|ghabra\w*|darr\w*|dar\s+lag\w*|tension)\b",
    "excitement": r"\b(excited|amazing|can'?t\s+wait|thrilled|wow|jackpot|rich|lalach|utsahit|mazaa)\b",
    "fomo": r"\b(miss\s+(out|the)|left\s+behind|regret|chhoot|mauka\s+(chala|nikal)|don'?t\s+want\s+to\s+miss)\b",
    "anger": r"\b(angry|furious|annoyed|gussa|irritated|cheated|dhokha)\b",
    "calm": r"\b(calm\w*|relaxed|composed|steady|shaant|thanda|sukoon)\b",
    "regret": r"\b(regret|should\s+have|pachta\w*|afsos)\b",
}

_UNCERT = re.compile(BEHAVIOURS["uncertainty_acknowledgement"]["patterns"][0], I)
_SKEPTIC = re.compile(r"(scam|fraud|fake|suspicious|red\s*flag|too\s+good|nobody\s+can|no\s+one\s+can|not\s+(proof|evidence|enough)|can'?t\s+be\s+(true|guaranteed)|"
                      r"shak|thagi|nakli|dhokha|doubt|isn'?t\s+(proof|evidence)|not\s+independent|saboot\s+nahi)", I)
# negative behaviours are suppressed when the same sentence is clearly sceptical about the very thing mentioned
_SUPPRESS_IF_SKEPTIC = {"social_proof_reliance", "friend_reliance", "authority_reliance", "urgency_reaction", "greed_driven", "overconfidence"}


@dataclass
class BehaviourHit:
    label: str
    confidence: float
    source: str      # rule | context | ml
    evidence: str = ""


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?;])\s+|\n+", text, flags=I)
    return [p.strip() for p in parts if p and p.strip()]


def emotional_indicators(text: str) -> list[str]:
    return [k for k, p in EMOTION_PATTERNS.items() if re.search(p, text or "", I)]


def has_uncertainty_recognition(text: str) -> bool:
    return bool(_UNCERT.search(text or ""))


def classify_rules(text: str) -> list[BehaviourHit]:
    text = text or ""
    hits: dict[str, BehaviourHit] = {}
    for sent in _sentences(text):
        skeptical = bool(_SKEPTIC.search(sent))
        for label, spec in BEHAVIOURS.items():
            if label in _SUPPRESS_IF_SKEPTIC and skeptical:
                continue
            for pat in spec["patterns"]:
                m = re.search(pat, sent, I)
                if m:
                    hits.setdefault(label, BehaviourHit(label, 0.8, "rule", m.group(0)[:80]))
                    break
    return list(hits.values())


def classify_context(quality: str, pressure_types: list[str], latency_ms: int | None, recall: float | None,
                     requested_evidence: bool, verification: bool | None) -> list[BehaviourHit]:
    """Behaviour implied by the decision itself (not the words)."""
    out: list[BehaviourHit] = []
    p = set(pressure_types)
    if quality == "unsafe":
        if p & {"social_proof", "peer_pressure"}:
            out.append(BehaviourHit("social_proof_reliance", 0.6, "context", "unsafe choice under social pressure"))
        if p & {"urgency", "countdown", "scarcity", "fomo"}:
            out.append(BehaviourHit("urgency_reaction", 0.65, "context", "unsafe choice under time pressure"))
        if p & {"authority"}:
            out.append(BehaviourHit("authority_reliance", 0.6, "context", "unsafe choice after authority claim"))
        if p & {"loss_recovery"}:
            out.append(BehaviourHit("loss_chasing", 0.7, "context", "unsafe choice under loss-recovery pressure"))
        if p & {"fear"}:
            out.append(BehaviourHit("fear_panic", 0.6, "context", "unsafe choice under fear"))
        if p & {"greed"}:
            out.append(BehaviourHit("greed_driven", 0.6, "context", "unsafe choice under greed pressure"))
        if latency_ms is not None and latency_ms < 4000 and p:
            out.append(BehaviourHit("urgency_reaction", 0.7, "context", f"decided in {latency_ms / 1000:.1f}s under pressure"))
    if quality == "safe" and p:
        out.append(BehaviourHit("deliberate_pause", 0.55, "context", "safe choice under pressure"))
    if requested_evidence or verification:
        out.append(BehaviourHit("evidence_seeking", 0.8, "context", "requested or performed verification"))
    if recall is not None and recall >= 0.6:
        out.append(BehaviourHit("evidence_seeking", 0.6, "context", "noticed most warning signs"))
    return out


def merge(*groups: list[BehaviourHit]) -> list[BehaviourHit]:
    best: dict[str, BehaviourHit] = {}
    for g in groups:
        for h in g:
            cur = best.get(h.label)
            if cur is None or h.confidence > cur.confidence:
                best[h.label] = h
            elif cur and h.source != cur.source:
                cur.source = "+".join(sorted(set(cur.source.split("+")) | {h.source}))
                cur.confidence = min(0.97, max(cur.confidence, h.confidence) + 0.05)
    return sorted(best.values(), key=lambda h: -h.confidence)


def explain(label: str, lang: str = "en") -> dict:
    spec = BEHAVIOURS[label]
    lang = lang if lang in ("en", "hinglish", "hi") else "en"
    return {"label": label, "name": spec["name"], "positive": spec["positive"], "explanation": spec["explain"][lang],
            "dimension": spec["dimension"]}
