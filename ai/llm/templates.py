"""Deterministic explanation templates: the guaranteed (no-LLM) path. All text is supportive and non-judgemental."""
from __future__ import annotations

PRESSURE_NAMES = {
    "en": {"urgency": "urgency", "countdown": "a countdown", "scarcity": "scarcity", "social_proof": "social proof", "authority": "authority claims",
           "fomo": "fear of missing out", "fear": "fear", "greed": "greed", "loss_recovery": "loss-recovery pressure", "peer_pressure": "peer pressure",
           "emotional_story": "an emotional story"},
    "hinglish": {"urgency": "jaldi ka dabaav", "countdown": "countdown", "scarcity": "kami ka dabaav", "social_proof": "social proof", "authority": "authority ke daave",
                 "fomo": "chhoot jaane ka darr", "fear": "darr", "greed": "laalach", "loss_recovery": "nuksaan wapas paane ka dabaav", "peer_pressure": "dostoon ka dabaav",
                 "emotional_story": "bhavnaatmak kahani"},
    "hi": {"urgency": "जल्दबाज़ी", "countdown": "काउंटडाउन", "scarcity": "कमी का दबाव", "social_proof": "सामाजिक प्रमाण", "authority": "अधिकार के दावे",
           "fomo": "छूट जाने का डर", "fear": "डर", "greed": "लालच", "loss_recovery": "नुकसान की भरपाई का दबाव", "peer_pressure": "साथियों का दबाव",
           "emotional_story": "भावनात्मक कहानी"},
}

T = {
    "en": {
        "safe": "A strong choice.", "mixed": "A reasonable step — with room to go further.",
        "unsafe": "This is a very common reaction, and exactly what this scenario is designed to practise.",
        "noticed": "You noticed {n} of {total} warning signs, including “{label}”.",
        "noticed_none": "You didn't mark any warning signs this time.",
        "missed": "Worth a second look: “{label}”.",
        "pressure_safe": "You held steady under {types}.", "pressure_unsafe": "Pressure from {types} was strong here — that is the point of the exercise.",
        "pressure_mixed": "You partly held steady under {types}.",
        "behaviour": "Pattern noticed: {name}.", "positive": "What worked: {name}.",
        "misc": "{name}: {correction}",
        "confidence_high_unsafe": "You felt very sure ({c}/5). Strong certainty is a good moment to double-check.",
        "confidence_low_safe": "You were cautious ({c}/5) and that served you well.",
    },
    "hinglish": {
        "safe": "Ek mazboot faisla.", "mixed": "Ek theek kadam — par aur aage jaa sakte hain.",
        "unsafe": "Ye bahut aam pratikriya hai, aur isi ka abhyas ye scenario karata hai.",
        "noticed": "Aapne {total} mein se {n} chetavani sanket pehchane, jaise “{label}”.",
        "noticed_none": "Is baar aapne koi chetavani sanket mark nahi kiya.",
        "missed": "Dobara dekhne layak: “{label}”.",
        "pressure_safe": "{types} ke dabaav mein aap sthir rahe.", "pressure_unsafe": "Yahan {types} ka dabaav tez tha — abhyas ka maksad yahi hai.",
        "pressure_mixed": "{types} ke dabaav mein aap kuch had tak sthir rahe.",
        "behaviour": "Dikha pattern: {name}.", "positive": "Jo kaam aaya: {name}.",
        "misc": "{name}: {correction}",
        "confidence_high_unsafe": "Aap bahut pakke the ({c}/5). Zyada vishwas dobara check karne ka achha samay hai.",
        "confidence_low_safe": "Aap saavdhaan the ({c}/5) aur ye kaam aaya.",
    },
    "hi": {
        "safe": "एक मज़बूत फ़ैसला।", "mixed": "एक ठीक कदम — पर और आगे जा सकते हैं।",
        "unsafe": "यह बहुत आम प्रतिक्रिया है, और इसी का अभ्यास यह परिदृश्य कराता है।",
        "noticed": "आपने {total} में से {n} चेतावनी संकेत पहचाने, जैसे “{label}”।",
        "noticed_none": "इस बार आपने कोई चेतावनी संकेत चिह्नित नहीं किया।",
        "missed": "दोबारा देखने लायक: “{label}”।",
        "pressure_safe": "{types} के दबाव में आप स्थिर रहे।", "pressure_unsafe": "यहाँ {types} का दबाव तेज़ था — अभ्यास का मक़सद यही है।",
        "pressure_mixed": "{types} के दबाव में आप कुछ हद तक स्थिर रहे।",
        "behaviour": "दिखा पैटर्न: {name}।", "positive": "जो काम आया: {name}।",
        "misc": "{name}: {correction}",
        "confidence_high_unsafe": "आप बहुत पक्के थे ({c}/5)। ज़्यादा विश्वास दोबारा जाँचने का अच्छा समय है।",
        "confidence_low_safe": "आप सावधान थे ({c}/5) और यह काम आया।",
    },
}


def build_explanation(facts: dict, lang: str = "en") -> str:
    lang = lang if lang in T else "en"
    t = T[lang]
    parts: list[str] = [t[facts["quality"]]]
    nt = facts.get("noticed") or []
    total = facts.get("red_flag_total") or 0
    if total:
        parts.append(t["noticed"].format(n=len(nt), total=total, label=nt[0]["label"]) if nt else t["noticed_none"])
    missed = facts.get("missed") or []
    if missed:
        mi = missed[0]
        parts.append(t["missed"].format(label=mi["label"]))
    types = facts.get("pressure_types") or []
    if types:
        names = ", ".join(PRESSURE_NAMES[lang].get(x, x) for x in dict.fromkeys(types))
        parts.append(t[f"pressure_{facts['quality']}"].format(types=names))
    beh = facts.get("behaviours") or []
    neg = next((b for b in beh if not b["positive"]), None)
    pos = next((b for b in beh if b["positive"]), None)
    if neg:
        parts.append(t["behaviour"].format(name=neg["name"]))
    if pos and facts["quality"] != "unsafe":
        parts.append(t["positive"].format(name=pos["name"]))
    mis = facts.get("misconceptions") or []
    if mis:
        parts.append(t["misc"].format(name=mis[0]["name"], correction=mis[0]["correction"]))
    c = facts.get("confidence")
    if c is not None:
        if c >= 4 and facts["quality"] == "unsafe":
            parts.append(t["confidence_high_unsafe"].format(c=c))
        elif c <= 2 and facts["quality"] == "safe":
            parts.append(t["confidence_low_safe"].format(c=c))
    return " ".join(p for p in parts if p)
