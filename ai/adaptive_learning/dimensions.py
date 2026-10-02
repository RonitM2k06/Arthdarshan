"""Names and non-judgemental phrasing for the ten Financial Resilience Fingerprint dimensions."""
from __future__ import annotations

DIMS: dict[str, dict] = {
    "concept_knowledge": {
        "name": {"en": "Financial Concept Knowledge", "hinglish": "Financial Concepts ki Samajh", "hi": "वित्तीय अवधारणाओं की समझ"},
        "short": {"en": "Concepts", "hinglish": "Concepts", "hi": "अवधारणाएँ"},
        "strength": {"en": "understanding how core ideas such as fees, risk and diversification work",
                     "hinglish": "fees, risk aur diversification jaise mool vichar samajhna",
                     "hi": "शुल्क, जोखिम और विविधीकरण जैसे मूल विचार समझना"},
        "opportunity": {"en": "connecting core ideas such as fees, risk and diversification to real consequences",
                        "hinglish": "fees, risk aur diversification jaise vichar asli nateejon se jodna",
                        "hi": "शुल्क, जोखिम और विविधीकरण जैसे विचारों को असली नतीजों से जोड़ना"}},
    "risk_recognition": {
        "name": {"en": "Risk Recognition", "hinglish": "Risk Pehchaan", "hi": "जोखिम की पहचान"},
        "short": {"en": "Risk", "hinglish": "Risk", "hi": "जोखिम"},
        "strength": {"en": "spotting obvious warning signs and risk", "hinglish": "saaf chetavani ke sanket aur risk pehchanna", "hi": "साफ़ चेतावनी संकेत और जोखिम पहचानना"},
        "opportunity": {"en": "noticing less obvious warning signs and sources of risk", "hinglish": "kam saaf chetavani ke sanket aur risk ke sroton ko dekhna", "hi": "कम स्पष्ट चेतावनी संकेतों और जोखिम के स्रोतों को देखना"}},
    "evidence_verification": {
        "name": {"en": "Evidence Verification", "hinglish": "Saboot ki Jaanch", "hi": "सबूत की जाँच"},
        "short": {"en": "Verification", "hinglish": "Jaanch", "hi": "जाँच"},
        "strength": {"en": "checking claims through independent sources", "hinglish": "daavon ko swatantra sroton se check karna", "hi": "दावों को स्वतंत्र स्रोतों से जाँचना"},
        "opportunity": {"en": "verifying claims independently, especially when an authority is claimed",
                        "hinglish": "daavon ko swatantra roop se verify karna, khaaskar jab koi authority ka daava ho", "hi": "दावों को स्वतंत्र रूप से सत्यापित करना, खासकर जब अधिकार का दावा हो"}},
    "scam_awareness": {
        "name": {"en": "Scam Awareness", "hinglish": "Scam ki Pehchaan", "hi": "ठगी की पहचान"},
        "short": {"en": "Scams", "hinglish": "Scam", "hi": "ठगी"},
        "strength": {"en": "recognising scam patterns such as guaranteed returns and fees to withdraw", "hinglish": "guaranteed returns aur withdraw ki fee jaise scam pattern pehchanna", "hi": "गारंटीशुदा रिटर्न और निकासी शुल्क जैसे ठगी के पैटर्न पहचानना"},
        "opportunity": {"en": "recognising how scams escalate and disguise themselves", "hinglish": "scams kaise badhte hain aur bhesh badalte hain, ye pehchanna", "hi": "ठगी कैसे बढ़ती और भेष बदलती है, यह पहचानना"}},
    "fomo_resistance": {
        "name": {"en": "FOMO Resistance", "hinglish": "FOMO se Bachav", "hi": "FOMO से बचाव"},
        "short": {"en": "FOMO", "hinglish": "FOMO", "hi": "FOMO"},
        "strength": {"en": "staying steady under urgency, countdowns and scarcity", "hinglish": "jaldi, countdown aur kami ke dabaav mein sthir rehna", "hi": "जल्दबाज़ी, काउंटडाउन और कमी के दबाव में स्थिर रहना"},
        "opportunity": {"en": "resisting urgency, countdowns and scarcity", "hinglish": "jaldi, countdown aur kami ke dabaav ka saamna karna", "hi": "जल्दबाज़ी, काउंटडाउन और कमी का सामना करना"}},
    "herd_resistance": {
        "name": {"en": "Herd Behaviour Resistance", "hinglish": "Bheed ke Dabaav se Bachav", "hi": "भीड़-चाल से बचाव"},
        "short": {"en": "Herd", "hinglish": "Bheed", "hi": "भीड़"},
        "strength": {"en": "not treating other people's participation as proof", "hinglish": "doosron ke judne ko saboot na maanna", "hi": "दूसरों के जुड़ने को सबूत न मानना"},
        "opportunity": {"en": "separating social proof and friends' opinions from independent evidence", "hinglish": "social proof aur dostoon ki raay ko swatantra saboot se alag karna", "hi": "सामाजिक प्रमाण और दोस्तों की राय को स्वतंत्र सबूत से अलग करना"}},
    "emotional_discipline": {
        "name": {"en": "Emotional Discipline", "hinglish": "Bhavnaon par Sanyam", "hi": "भावनात्मक अनुशासन"},
        "short": {"en": "Emotions", "hinglish": "Bhavna", "hi": "भावना"},
        "strength": {"en": "pausing when fear, greed or loss pressure is high", "hinglish": "darr, laalach ya nuksaan ke dabaav mein ruk jaana", "hi": "डर, लालच या नुकसान के दबाव में रुक जाना"},
        "opportunity": {"en": "pausing before acting under fear, greed or loss pressure", "hinglish": "darr, laalach ya nuksaan ke dabaav mein kadam se pehle ruk jaana", "hi": "डर, लालच या नुकसान के दबाव में कदम से पहले रुकना"}},
    "independent_reasoning": {
        "name": {"en": "Independent Reasoning", "hinglish": "Swatantra Soch", "hi": "स्वतंत्र चिंतन"},
        "short": {"en": "Reasoning", "hinglish": "Soch", "hi": "चिंतन"},
        "strength": {"en": "basing decisions on reasons you can examine yourself", "hinglish": "un karanon par faisle lena jinhe aap khud parakh sakte ho", "hi": "उन कारणों पर फ़ैसले लेना जिन्हें आप खुद परख सकें"},
        "opportunity": {"en": "building decisions on evidence rather than on what others say", "hinglish": "doosron ke kehne ki jagah saboot par faisle banana", "hi": "दूसरों के कहने की जगह सबूत पर फ़ैसले बनाना"}},
    "uncertainty_awareness": {
        "name": {"en": "Uncertainty Awareness", "hinglish": "Anishchitta ki Samajh", "hi": "अनिश्चितता की समझ"},
        "short": {"en": "Uncertainty", "hinglish": "Anishchitta", "hi": "अनिश्चितता"},
        "strength": {"en": "recognising what cannot be known and matching confidence to evidence", "hinglish": "ye pehchanna ki kya nahi jaana ja sakta aur vishwas ko saboot se milana", "hi": "यह पहचानना कि क्या नहीं जाना जा सकता और विश्वास को सबूत से मिलाना"},
        "opportunity": {"en": "matching confidence to evidence and accepting what cannot be known", "hinglish": "vishwas ko saboot se milana aur jo jaana nahi ja sakta use maanna", "hi": "विश्वास को सबूत से मिलाना और जो जाना नहीं जा सकता उसे मानना"}},
    "terminology": {
        "name": {"en": "Financial Terminology Understanding", "hinglish": "Financial Shabdon ki Samajh", "hi": "वित्तीय शब्दावली की समझ"},
        "short": {"en": "Terminology", "hinglish": "Shabd", "hi": "शब्दावली"},
        "strength": {"en": "understanding terms like NAV, exit load and yield", "hinglish": "NAV, exit load aur yield jaise shabd samajhna", "hi": "NAV, एग्ज़िट लोड और यील्ड जैसे शब्द समझना"},
        "opportunity": {"en": "understanding terms like NAV, exit load and yield in plain language", "hinglish": "NAV, exit load aur yield jaise shabd saral bhasha mein samajhna", "hi": "NAV, एग्ज़िट लोड और यील्ड जैसे शब्द सरल भाषा में समझना"}},
}


def lang_of(lang: str) -> str:
    return lang if lang in ("en", "hinglish", "hi") else "en"


def name(dim: str, lang: str = "en") -> str:
    return DIMS[dim]["name"][lang_of(lang)]
