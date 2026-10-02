"""Evidence Lab: structured, rule-based reading of a financial claim.

It does NOT rule on whether something is a scam. It lists which signals are present, what is missing, and what the
learner should verify independently, following: CLAIM -> SOURCE -> AUTHORITY -> EVIDENCE -> INDEPENDENT VERIFICATION -> DECISION.
"""
from __future__ import annotations

import re

I = re.IGNORECASE

SIGNALS: dict[str, dict] = {
    "guarantee": {"q": "guarantee", "patterns": [r"guarante\w*", r"gaurant\w*", r"assured\s+returns?", r"risk[\s-]*free", r"\bno\s+risk\b", r"100\s*%\s*safe", r"pakka\s+(return|munafa|profit)", r"sure[\s-]*shot", r"fixed\s+returns?"],
                  "en": "A guarantee or 'no risk' promise.", "hinglish": "Guarantee ya 'no risk' ka vaada.", "hi": "गारंटी या 'कोई जोखिम नहीं' का वादा।",
                  "verify": {"en": "Ask: what exactly backs this promise, in writing? Market-linked returns cannot honestly be guaranteed.", "hinglish": "Poochho: is vaade ke peeche kya hai, likhit mein? Market-linked returns sach mein guarantee nahi ho sakte.", "hi": "पूछें: इस वादे के पीछे क्या है, लिखित में? बाज़ार-आधारित रिटर्न की ईमानदारी से गारंटी नहीं हो सकती।"}},
    "high_return": {"q": "evidence", "patterns": [r"\b(\d{2,3})\s*%\s*(returns?|profit|monthly|weekly|per\s+(month|week|year)|p\.?a\.?)", r"double\s+(your\s+)?money", r"\bdaily\s+(profit|income)", r"(returns?|munafa)\s+(of\s+)?\d{2,3}\s*%"],
                    "en": "A very high return figure.", "hinglish": "Bahut ooncha return figure.", "hi": "बहुत ऊँचा रिटर्न आँकड़ा।",
                    "verify": {"en": "Compare with the idea that higher promised returns usually mean higher risk or a false promise.", "hinglish": "Yaad rakho: zyada vaada kiya gaya return aksar zyada risk ya jhootha vaada hota hai.", "hi": "याद रखें: ज़्यादा वादा किया गया रिटर्न अक्सर ज़्यादा जोखिम या झूठा वादा होता है।"}},
    "urgency": {"q": "urgency", "patterns": [r"\btoday\s+only\b", r"\binvest\s+today\b", r"\bhurry\b", r"\blast\s+chance\b", r"\bact\s+now\b", r"\blimited\s+(time|period|offer)\b", r"\bexpires?\s+(today|tonight|soon)\b", r"within\s+\d+\s+(minutes?|hours?)", r"aaj\s+hi", r"jaldi", r"abhi\s+(invest|join|kar)", r"closes?\s+in"],
                "en": "Urgency or a deadline.", "hinglish": "Jaldi ya deadline.", "hi": "जल्दबाज़ी या समय-सीमा।",
                "verify": {"en": "A real, regulated product does not need a decision in minutes. Wait, then verify.", "hinglish": "Asli, regulated product ko minutes mein faisla nahi chahiye. Ruko, phir verify karo.", "hi": "असली, विनियमित उत्पाद को मिनटों में फ़ैसला नहीं चाहिए। रुकें, फिर सत्यापित करें।"}},
    "scarcity": {"q": "urgency", "patterns": [r"only\s+\d+\s+(slots?|seats?|spots?|places?)", r"\bslots?\s+(left|remaining|filling)", r"limited\s+(slots?|seats?|spots?)", r"sirf\s+\d+\s+(slots?|seats?)", r"\bexclusive\b"],
                 "en": "Artificial scarcity (few slots).", "hinglish": "Banavati kami (kam slots).", "hi": "बनावटी कमी (कम स्लॉट)।",
                 "verify": {"en": "Scarcity that changes when you hesitate is scripted, not a fact.", "hinglish": "Jo kami aapke hichkichane par badle wo scripted hai, tathya nahi.", "hi": "जो कमी आपके हिचकिचाने पर बदले वह स्क्रिप्ट है, तथ्य नहीं।"}},
    "authority": {"q": "authority", "patterns": [r"\b(sebi|rbi|government|govt)\s+(registered|approved|certified|authori[sz]ed)", r"\bregistered\s+(with|by)\b", r"\bcertified\b", r"\bofficially\s+approved\b", r"\bex[\s-]*(fund\s+manager|banker)", r"\bexpert\b", r"sarkari"],
                  "en": "A claim of authority, registration or expertise.", "hinglish": "Authority, registration ya expertise ka daava.", "hi": "अधिकार, पंजीकरण या विशेषज्ञता का दावा।",
                  "verify": {"en": "Look the registration up yourself on the regulator's official website (typed by you). A number or certificate sent by the seller proves nothing.", "hinglish": "Registration ko regulator ki official website par khud (khud type karke) dekho. Seller ka bheja number ya certificate kuch sabit nahi karta.", "hi": "पंजीकरण को नियामक की आधिकारिक वेबसाइट पर खुद (खुद टाइप करके) देखें। विक्रेता का भेजा नंबर या प्रमाणपत्र कुछ साबित नहीं करता।"}},
    "social_proof": {"q": "evidence", "patterns": [r"\b\d[\d,]*\+?\s*(members|people|investors|users|customers)\b", r"\beveryone\s+(is|are)\b", r"already\s+(joined|invested|earned)", r"\btestimonials?\b", r"screenshots?", r"sab\s+log", r"\bsuccess\s+stories\b"],
                     "en": "Social proof (crowds, testimonials, screenshots).", "hinglish": "Social proof (bheed, testimonials, screenshots).", "hi": "सामाजिक प्रमाण (भीड़, प्रशंसापत्र, स्क्रीनशॉट)।",
                     "verify": {"en": "Crowds and screenshots are easy to fake and selected by the seller. Ask for independent, verifiable records including losses.", "hinglish": "Bheed aur screenshots nakli banana aasan hai aur seller chunta hai. Nuksaan samet swatantra, jaanch-yogya record maango.", "hi": "भीड़ और स्क्रीनशॉट नकली बनाना आसान है और विक्रेता चुनता है। नुकसान सहित स्वतंत्र, जाँचने योग्य रिकॉर्ड माँगें।"}},
    "payment": {"q": "source", "patterns": [r"\b(pay|send|transfer|deposit)\b[^.!?]{0,40}\b(upi|account|wallet|gpay|phonepe|paytm|qr)\b", r"\bregistration\s+fee\b", r"\bverification\s+fee\b", r"\bprocessing\s+fee\b", r"\bfee\s+(before|to)\s+(withdraw|release)", r"\bsecurity\s+deposit\b", r"@(ybl|okaxis|oksbi|paytm|upi)\b"],
                "en": "A payment request, possibly to an individual or before you can withdraw.", "hinglish": "Payment ki maang, shayad kisi vyakti ko ya nikalne se pehle.", "hi": "भुगतान की माँग, शायद किसी व्यक्ति को या निकासी से पहले।",
                "verify": {"en": "Genuine firms collect through accounts in the company's name with receipts. Never pay a fee to release your own money.", "hinglish": "Asli firms company ke naam ke account mein receipt ke saath leti hain. Apna paisa nikalne ke liye kabhi fee mat do.", "hi": "असली फ़र्में कंपनी के नाम के खाते में रसीद के साथ लेती हैं। अपना पैसा निकालने के लिए कभी शुल्क न दें।"}},
    "secrecy": {"q": "source", "patterns": [r"\b(don'?t|do\s+not)\s+(tell|share)\b", r"\bkeep\s+(it\s+)?(secret|confidential)", r"\bprivate\s+(group|tip|channel)", r"\bmembers\s+only\b", r"kisi\s+ko\s+mat\s+batana"],
               "en": "Secrecy or 'members only' framing.", "hinglish": "Gopniyata ya 'sirf members' ka dhaancha.", "hi": "गोपनीयता या 'केवल सदस्य' का ढाँचा।",
               "verify": {"en": "Secrecy stops others from questioning the claim. Discuss it with someone you trust.", "hinglish": "Gopniyata dusron ko sawaal karne se rokti hai. Kisi bharosemand se baat karo.", "hi": "गोपनीयता दूसरों को सवाल करने से रोकती है। किसी भरोसेमंद से बात करें।"}},
    "unsolicited": {"q": "source", "patterns": [r"\b(added|invited)\s+you\b", r"\bcongratulations\b", r"\byou\s+(have\s+been\s+)?(selected|chosen)\b", r"\bdear\s+(investor|customer|sir|madam)\b", r"\bwhatsapp\s+group\b", r"\btelegram\b"],
                    "en": "Unsolicited contact or channel (you did not ask for this).", "hinglish": "Bin-bulaya sampark ya channel (aapne maanga nahi tha).", "hi": "बिन-बुलाया संपर्क या चैनल (आपने माँगा नहीं था)।",
                    "verify": {"en": "Ask yourself: did I start this contact? If not, treat the claim as unverified.", "hinglish": "Khud se poochho: kya sampark maine shuru kiya? Nahi, to daave ko unverified maano.", "hi": "खुद से पूछें: क्या संपर्क मैंने शुरू किया? नहीं, तो दावे को अनजाँचा मानें।"}},
}

MISSING_CHECKS = [
    ("who", r"\b(pvt|ltd|llp|limited|company|inc\.?|corp)\b|\b(cin|gstin|registration\s+(no|number)|licen[cs]e)\b",
     {"en": "Who is responsible? No company name, registration or licence details were given.", "hinglish": "Zimmedar kaun hai? Company ka naam, registration ya licence vivaran nahi diya gaya.", "hi": "ज़िम्मेदार कौन है? कंपनी का नाम, पंजीकरण या लाइसेंस विवरण नहीं दिया गया।"}),
    ("risk", r"\b(risk|loss|losses|may\s+fall|can\s+fall|not\s+guaranteed|nuksaan|jokhim)\b",
     {"en": "What can go wrong? No risks or possible losses were mentioned.", "hinglish": "Kya galat ho sakta hai? Koi risk ya sambhavit nuksaan nahi bataya gaya.", "hi": "क्या गलत हो सकता है? कोई जोखिम या संभावित नुकसान नहीं बताया गया।"}),
    ("cost", r"\b(fees?|charges?|expense\s+ratio|commission|load|kharcha|shulk)\b",
     {"en": "What does it cost? No fees or charges were described.", "hinglish": "Ismein kharcha kya hai? Koi fee ya charge nahi bataya gaya.", "hi": "इसमें खर्च क्या है? कोई शुल्क या चार्ज नहीं बताया गया।"}),
    ("exit", r"\b(withdraw\w*|redeem|redemption|exit|lock[\s-]*in|nikal\w*)\b",
     {"en": "How and when can you withdraw? Withdrawal terms were not described.", "hinglish": "Aap kab aur kaise nikal sakte ho? Nikalne ki sharten nahi bataayi gayi.", "hi": "आप कब और कैसे निकाल सकते हैं? निकासी की शर्तें नहीं बताई गईं।"}),
]

WORKFLOW = [
    {"step": "CLAIM", "en": "Write down exactly what is promised.", "hinglish": "Likho ki theek-theek kya vaada hai.", "hi": "ठीक-ठीक लिखें कि क्या वादा है।"},
    {"step": "SOURCE", "en": "Who is saying it, and did you ask them?", "hinglish": "Kaun keh raha hai, aur kya aapne pucha tha?", "hi": "कौन कह रहा है, और क्या आपने पूछा था?"},
    {"step": "AUTHORITY", "en": "Is any claimed registration or expertise checkable?", "hinglish": "Kya daava kiya gaya registration ya expertise check ho sakta hai?", "hi": "क्या दावा किया गया पंजीकरण या विशेषज्ञता जाँची जा सकती है?"},
    {"step": "EVIDENCE", "en": "What independent proof exists beyond the seller's own material?", "hinglish": "Seller ke apne material ke alawa swatantra saboot kya hai?", "hi": "विक्रेता की अपनी सामग्री के अलावा स्वतंत्र सबूत क्या है?"},
    {"step": "INDEPENDENT VERIFICATION", "en": "Check through a source the seller does not control.", "hinglish": "Aise source se check karo jise seller control nahi karta.", "hi": "ऐसे स्रोत से जाँचें जिसे विक्रेता नियंत्रित नहीं करता।"},
    {"step": "DECISION", "en": "Decide only after the check. If you cannot verify it, do not pay.", "hinglish": "Jaanch ke baad hi faisla. Verify na ho to paise mat do.", "hi": "जाँच के बाद ही फ़ैसला। सत्यापित न हो तो भुगतान न करें।"}]

QUESTIONS = [
    ("who", {"en": "Who made the claim?", "hinglish": "Daava kisne kiya?", "hi": "दावा किसने किया?"}, ["unsolicited", "secrecy", "payment"]),
    ("urgency", {"en": "Is there urgency?", "hinglish": "Kya jaldi ka dabaav hai?", "hi": "क्या जल्दबाज़ी का दबाव है?"}, ["urgency", "scarcity"]),
    ("guarantee", {"en": "Is there a guarantee?", "hinglish": "Kya guarantee ka vaada hai?", "hi": "क्या गारंटी का वादा है?"}, ["guarantee", "high_return"]),
    ("evidence", {"en": "What evidence exists?", "hinglish": "Kya saboot hai?", "hi": "क्या सबूत है?"}, ["authority", "social_proof"]),
]


def _lang(lang: str) -> str:
    return lang if lang in ("en", "hinglish", "hi") else "en"


def analyze(text: str, lang: str = "en") -> dict:
    lang = _lang(lang)
    t = text or ""
    found: dict[str, str] = {}
    for key, spec in SIGNALS.items():
        for p in spec["patterns"]:
            mt = re.search(p, t, I)
            if mt:
                found[key] = mt.group(0)[:60]
                break
    questions = []
    for qid, qtext, keys in QUESTIONS:
        hits = [k for k in keys if k in found]
        questions.append({"id": qid, "question": qtext[lang], "signals": [{"id": k, "text": SIGNALS[k][lang], "matched": found[k]} for k in hits],
                          "answer": ("; ".join(SIGNALS[k][lang] for k in hits)) if hits else {"en": "Nothing obvious found in this text — which is not the same as safe.", "hinglish": "Is text mein kuch saaf nahi mila — iska matlab surakshit hona nahi.", "hi": "इस टेक्स्ट में कुछ स्पष्ट नहीं मिला — इसका मतलब सुरक्षित होना नहीं है।"}[lang]})
    missing = [{"id": mid, "text": msg[lang]} for mid, pat, msg in MISSING_CHECKS if not re.search(pat, t, I)]
    verify = [{"signal": k, "action": SIGNALS[k]["verify"][lang]} for k in found]
    verify.append({"signal": "always", "action": {"en": "Look up the entity yourself on the regulator's official website, typed by you — never via a link from the message.",
                                                   "hinglish": "Entity ko regulator ki official website par khud type karke dekho — message ke link se kabhi nahi.",
                                                   "hi": "संस्था को नियामक की आधिकारिक वेबसाइट पर खुद टाइप करके देखें — संदेश के लिंक से कभी नहीं।"}[lang]})
    n = len(found)
    level = "many" if n >= 4 else "several" if n >= 2 else "few" if n == 1 else "none"
    summary = {
        "many": {"en": f"{n} warning signals are present together. Treat this as unverified and do not pay until each is checked independently.",
                 "hinglish": f"{n} chetavani sanket ek saath maujood hain. Ise unverified maanein aur har ek swatantra roop se check hone tak paise na dein.",
                 "hi": f"{n} चेतावनी संकेत एक साथ मौजूद हैं। इसे अनजाँचा मानें और हर एक स्वतंत्र रूप से जाँचे जाने तक भुगतान न करें।"},
        "several": {"en": f"{n} warning signals are present. Verify each independently before any payment.", "hinglish": f"{n} chetavani sanket maujood hain. Kisi bhi payment se pehle har ek ko swatantra roop se verify karein.", "hi": f"{n} चेतावनी संकेत मौजूद हैं। किसी भी भुगतान से पहले हर एक को स्वतंत्र रूप से सत्यापित करें।"},
        "few": {"en": "One warning signal is present. It is worth verifying independently.", "hinglish": "Ek chetavani sanket maujood hai. Ise swatantra roop se verify karna theek rahega.", "hi": "एक चेतावनी संकेत मौजूद है। इसे स्वतंत्र रूप से सत्यापित करना उचित है।"},
        "none": {"en": "No common warning phrases were found in this text. That does not make it safe — the missing information below still needs checking.", "hinglish": "Is text mein aam chetavani shabd nahi mile. Iska matlab surakshit nahi — neeche ki gayab jaankari abhi bhi check karni hai.", "hi": "इस टेक्स्ट में आम चेतावनी शब्द नहीं मिले। इसका मतलब सुरक्षित नहीं — नीचे की अनुपस्थित जानकारी अभी भी जाँचनी है।"},
    }[level][lang]
    return {"signals_found": n, "level": level, "summary": summary, "questions": questions, "missing_information": missing,
            "verify_independently": verify, "workflow": [{"step": w["step"], "text": w[lang]} for w in WORKFLOW],
            "note": {"en": "This is a teaching aid, not a verdict. It reads only the words you pasted.", "hinglish": "Ye sikhane ka saadhan hai, faisla nahi. Ye sirf aapke diye shabdon ko padhta hai.", "hi": "यह सिखाने का साधन है, फ़ैसला नहीं। यह सिर्फ़ आपके दिए शब्दों को पढ़ता है।"}[lang]}


SAMPLES = [
    {"id": "tg", "title": "Telegram message (fictional)", "text": "SEBI registered opportunity. Guaranteed 30% returns. Only 10 slots remaining. Invest today."},
    {"id": "wa", "title": "WhatsApp forward (fictional)", "text": "Join Karan Sir's premium group for ₹3,000. 85% returns in last 3 months! 2,400 members. Screenshots inside. Do not share with non-members."},
    {"id": "fee", "title": "Withdrawal message (fictional)", "text": "Your profit is ready. Pay ₹2,000 verification fee to this UPI id to withdraw within 30 minutes or your profit expires."},
    {"id": "fund", "title": "A plain fund note (fictional)", "text": "Aakash Debt Opportunities Fund Pvt Ltd. Returns are not guaranteed and may fall; you may lose part of your money. Exit load 1% if redeemed within 12 months. Expense ratio and all charges are listed on page 6."},
]
