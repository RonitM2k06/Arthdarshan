"""Safety Gateway.

    USER INPUT -> check_input -> AI processing -> check_output -> SAFE RESPONSE

Rule-based and fully local, so it works with no LLM and cannot be talked out of its rules by a prompt.
Categories: recommendation, buy_sell_hold, prediction, personalized, broker_promotion, sensitive_data,
regulatory (unsupported claim), injection (attempts to override the rules).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .responses import INSUFFICIENT, safe_response

I = re.IGNORECASE

# --------------------------------------------------------------------------------------------------
# INPUT patterns: what a *user* is asking for
# --------------------------------------------------------------------------------------------------
_PRODUCT = r"(stocks?|shares?|mutual\s*funds?|funds?|etfs?|sips?|schemes?|crypto(currency)?|coins?|bitcoin|bonds?|ipos?|investments?|options|futures|commodit\w+|gold|silver|policy|plans?)"
_REC_PATTERNS = [
    rf"\b(which|what|whats|what's)\s+{_PRODUCT}\s+(should|shall|can|do|to|is|are|would|will|may)\b[^?.!]{{0,40}}(buy|invest|pick|choose|best|good|better|purchase|select|get|take|hold|sell)",
    rf"\b(which|what)\s+{_PRODUCT}\s+(is|are)\s+(the\s+)?(best|good|better|top|safest|right|ideal|great)",
    rf"\b(best|top|safest|highest[- ]returning|most profitable|number\s*one|no\.?\s*1)\s+{_PRODUCT}\b",
    rf"\b(recommend|suggest|advise|tip|pick)\w*\s+(me\s+|us\s+)?(a\s+|an\s+|any\s+|some\s+|the\s+|good\s+|best\s+)*{_PRODUCT}\b",
    rf"\b(give|tell|share|send)\s+(me\s+|us\s+)?(a\s+|an\s+|some\s+|the\s+)?(good\s+|best\s+|hot\s+|sure\s+|safe\s+)*(tips?|picks?|calls?|recommendations?|suggestions?)\b",
    rf"\b(multibagger|hot\s+tip|sure[- ]?shot|jackpot)\b",
    rf"\b(which|what)\s+{_PRODUCT}\s+to\s+(buy|invest|sell|hold|pick)",
    rf"\b(is\s+it\s+)?(good|safe|wise|right)\s+(time\s+)?to\s+(buy|sell|invest|enter|exit)\b",
    rf"\b(kaun\s*(sa|si)|konsa|kaunsa|kon\s*sa)\s+{_PRODUCT}\b[^?.!]{{0,40}}(lun|loon|kharidun|khareedun|kharidu|best|achha|accha|sahi|behtar|lena|le\s*lun|invest)",
    rf"\b{_PRODUCT}\s+(konsa|kaunsa|kaun\s*sa|kaun\s*si)\s+(best|achha|accha|sahi|behtar)",
    r"\b(kya|kab)\s+(kharidun|khareedun|bechun|kharidna|bechna|lena|becho|kharido|invest\s+karun|invest\s+karu)\b",
]
_BSH_PATTERNS = [
    r"\b(should|shall|can|must)\s+(i|we)\s+(buy|sell|hold|invest|exit|enter|switch|book\s+profit|average|accumulate|put)\b",
    r"\b(buy|sell|hold)\s+(or|/)\s*(buy|sell|hold)\b",
    r"\b(buy|sell|hold)\s+(now|today|tomorrow|this\s+week|kar\s*(du|dun|doon))\b",
    r"\b(kharidun|khareedun|bechun|becho|kharido)\s*\??\s*$",
    r"\bkya\s+(main|mai|hum)\s+(\w+\s+)?(kharid|bech|lagau|lagaun|invest)",
    r"\bbuy\s+(or\s+)?(sell\s+)?(kar|karu|karun)\b",
]
_PRED_PATTERNS = [
    r"\b(predict|prediction|forecast|projection|target\s+price|price\s+target)\b",
    r"\bwill\s+(the\s+)?(nifty|sensex|bank\s*nifty|market|markets|gold|silver|bitcoin|btc|ethereum|rupee|stock|share|price|\w+)\s+(go|rise|fall|crash|cross|reach|hit|touch|double|drop|increase|decrease|recover|jump|surge|tank)\b",
    r"\b(nifty|sensex|bank\s*nifty|gold|silver|bitcoin|crude|rupee|market|markets)\b[^?.!]{0,50}\b(tomorrow|next\s+(week|month|year|quarter|day)|by\s+(diwali|december|march|year[- ]end)|kal|parso|agle\s+(hafte|mahine|saal))\b",
    r"\b(kitna|kitne)\s+(badhega|girega|upar\s+jayega|neeche\s+jayega|chadhega|badhenge|girenge)\b",
    r"\b(market|nifty|sensex|share|stock)\s+(badhega|girega|crash\s+hoga|upar\s+jayega)\b",
    r"\bwhere\s+will\s+(the\s+)?(nifty|sensex|market|gold|bitcoin|price)\b",
    r"\bexpected\s+(returns?|gains?|profits?)\b",
    r"\bhow\s+much\s+(will|can)\s+(i|my\s+money|it)\s+(make|earn|grow|become|get)\b",
    r"\b(will|would)\s+i\s+(make|earn|get)\s+(a\s+)?(profit|money|returns?)\b",
]
_PERSONAL_PATTERNS = [
    r"\b(where|how)\s+(should|do|can|shall|would)\s+i\s+(invest|put|park|deploy|allocate|keep|use)\b",
    r"\b(i\s+have|i\s+got|my\s+savings?\s+(is|are)|with)\s*(₹|rs\.?|inr|rupees)?\s*[\d,\.]+\s*(k|l|lakh|lakhs|crore|cr|thousand)?\b[^?.!]{0,60}(invest|put|where|what\s+to\s+do|park|grow)",
    r"\b(invest|put|park)\s+(my\s+)?(₹|rs\.?|inr)?\s*[\d,\.]+\s*(k|l|lakh|lakhs|crore|cr|thousand)?\b[^?.!]{0,30}\b(where|in\s+what|kahan)",
    r"\b(tell|advise|suggest|guide)\s+(me\s+)?(where|how|what)\b[^?.!]{0,40}\b(invest|put\s+my|park)\b",
    r"\b(build|make|create|design|suggest|give)\s+(me\s+)?(a\s+|my\s+)?(portfolio|asset\s+allocation|investment\s+plan)\b",
    r"\b(how\s+should\s+i\s+allocate|my\s+portfolio\s+should)\b",
    r"\b(mere|meri)\s+paas\b[^?.!]{0,40}(hain|hai)\b[^?.!]{0,50}(kahan|kaha|kaise|kidhar)\s+(lagau|lagaun|lagana|invest|daalu|daalun)",
    r"\b(kahan|kaha|kidhar)\s+(invest|paisa\s+lagau|paisa\s+lagaun|paisa\s+lagana|lagau|lagaun|daalu|daalun)\b",
    r"\bpaisa\s+kahan\s+(lagana|lagau|lagaun|daalna)\b",
]
_BROKER_NAMES = (r"zerodha|kite|groww|upstox|angel\s*one|angel\s*broking|5\s*paisa|icici\s*direct|hdfc\s*securities|kotak\s*securities|paytm\s*money|"
                 r"sharekhan|motilal\s*oswal|dhan|fyers|robinhood|coinbase|binance|wazirx|coindcx|etoro|interactive\s*brokers|et\s*money|kuvera|"
                 r"smallcase|scripbox|mstock|alice\s*blue")
_BROKER_PATTERNS = [
    r"\b(which|what|best|top|good|better|safest|cheapest|recommend\w*)\s+(is\s+the\s+|are\s+the\s+)?(broker|brokers|demat|trading\s+app|investing\s+app|platform|brokerage|app)\b",
    rf"\b({_BROKER_NAMES})\b[^?.!]{{0,50}}\b(best|better|recommend|should\s+i|open\s+account|use|trust|safe|good|vs|versus|or)\b",
    rf"\b(best|better|recommend|should\s+i|open\s+(an\s+)?account|use|safe|good)\b[^?.!]{{0,50}}\b({_BROKER_NAMES})\b",
    r"\b(kaun\s*sa|konsa|kaunsa)\s+(broker|demat|app)\b",
]
_INJECTION_PATTERNS = [
    r"\b(ignore|forget|disregard|override|bypass)\s+(all\s+|your\s+|the\s+|previous\s+|prior\s+)*(instructions?|rules?|guardrails?|safety|restrictions?|prompt|policies|policy)\b",
    r"\b(act|behave|pretend|roleplay)\s+(as|like)\s+(a\s+|an\s+|my\s+)?(financial|investment|stock|sebi|certified)\s*(advisor|adviser|analyst|expert|guru|planner|broker)\b",
    r"\byou\s+are\s+now\s+(a\s+|an\s+)?(financial|investment|unrestricted|dan)\b",
    r"\b(pretend|imagine|act|behave)\s+(you\s+are|you're|as)\s+(my\s+|a\s+|an\s+)?[^.?!]{0,30}(advisor|adviser|analyst|expert|guru|planner|broker)\b",
    r"\bjailbreak\b|\bdeveloper\s+mode\b|\bdo\s+anything\s+now\b",
    r"\bfor\s+(educational|research|hypothetical|fictional)\s+purposes?[,:]?\s*(only\s*)?(tell|give|say|name|recommend|predict)\b",
    r"\bhypothetically\b[^?.!]{0,40}\b(which|what)\b[^?.!]{0,30}\b(stock|fund|share|crypto)\b[^?.!]{0,30}\b(buy|best)\b",
    r"\bsystem\s+prompt\b",
]

# --------------------------------------------------------------------------------------------------
# Sensitive data
# --------------------------------------------------------------------------------------------------
_PAN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
_AADHAAR = re.compile(r"(?<!\d)(?<!\d[\s-])[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}(?!\d)(?![\s-]\d)")
_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_OTP = re.compile(r"\b(otp|one[\s-]*time[\s-]*(password|code|pin)|verification\s*code|cvv|cvc)\b[^\d\n]{0,25}\d{3,8}\b", I)
_PIN = re.compile(r"\b(upi|atm|card|debit|credit|net\s*banking|mpin|m-pin|login|transaction)?\s*pin\b\s*(is|:|=|-)?\s*\d{4,6}\b", I)
_PASSWORD = re.compile(r"\b(password|passcode|passwd|pwd|login\s*id|net\s*banking)\b\s*(is|:|=|-)\s*\S{4,}", I)
_UPI_ID = re.compile(r"\b[\w.\-]{2,}@(ybl|okaxis|oksbi|okicici|okhdfcbank|paytm|upi|ibl|axl|apl|sbi|icici|hdfcbank|axisbank|barodampay|ikwik)\b", I)
_ACCOUNT_NO = re.compile(r"\b(account|a/c|acct|acc)\s*(no\.?|number|num|#)?\s*(is|:|=|-)?\s*\d{9,18}\b", I)
_IFSC = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


def find_sensitive(text: str) -> list[tuple[str, tuple[int, int]]]:
    hits: list[tuple[str, tuple[int, int]]] = []
    for name, rx in [("pan", _PAN), ("aadhaar", _AADHAAR), ("otp", _OTP), ("pin", _PIN), ("password", _PASSWORD),
                     ("upi_id", _UPI_ID), ("account_number", _ACCOUNT_NO), ("ifsc", _IFSC)]:
        for m in rx.finditer(text):
            hits.append((name, m.span()))
    for m in _CARD.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            hits.append(("card_number", m.span()))
    return hits


def redact(text: str) -> tuple[str, list[str]]:
    """Mask sensitive values. Returns (clean_text, kinds_found)."""
    hits = find_sensitive(text)
    if not hits:
        return text, []
    spans = sorted(hits, key=lambda h: h[1][0])
    out, last, kinds = [], 0, []
    for kind, (a, b) in spans:
        if a < last:
            continue
        out.append(text[last:a])
        out.append("[REDACTED]")
        last = b
        kinds.append(kind)
    out.append(text[last:])
    return "".join(out), sorted(set(kinds))


# --------------------------------------------------------------------------------------------------
# OUTPUT patterns: what generated text must never contain
# --------------------------------------------------------------------------------------------------
_OUT_ADVICE = [
    r"\b(you|u)\s+(should|must|ought\s+to|need\s+to|can\s+safely|could\s+consider)\s+(definitely\s+|certainly\s+|now\s+|simply\s+)?(buy|sell|invest\s+in|hold|put\s+(your|the)\s+money|switch\s+to|choose|pick|go\s+for|open\s+an?\s+account)\b",
    r"\bi\s+(would\s+|highly\s+|strongly\s+)?(recommend|suggest|advise)\s+(you\s+)?(to\s+|that\s+you\s+)?(buy|sell|invest|hold|choose|pick|go|put|open|use|switch|take)\b",
    r"\b(my|our)\s+(top\s+)?(pick|recommendation|suggestion|tip)\b",
    r"\b(is|are|looks?|seems?)\s+(a\s+|an\s+)?(good|great|strong|solid|excellent|smart|safe|best)\s+(buy|investment|bet|pick|choice|option)\b",
    r"\b(best|top|safest)\s+(stock|share|mutual\s*fund|fund|etf|crypto|investment|sip|broker|scheme)s?\s+(is|are|to\s+(buy|invest))\b",
    r"\b(buy|sell|accumulate|book\s+profit)\s+(it|this|that|these|the\s+stock|the\s+share|the\s+fund)\s+(now|today|immediately|on\s+dips?)\b",
    r"\b(go|stay)\s+(long|short)\b",
    r"\bput\s+(your\s+)?(money|savings|₹\s*[\d,]+|rs\.?\s*[\d,]+)\s+(in|into)\b",
    r"\ballocate\s+(\d+\s*%|your)\b",
]
_OUT_PREDICT = [
    r"\b(will|is\s+going\s+to|is\s+likely\s+to|is\s+expected\s+to|should)\s+(rise|increase|go\s+up|double|triple|fall|crash|drop|decline|recover|rally|surge|outperform|hit|reach|cross)\b[^.!?]{0,60}\b(by|to|in|next|tomorrow|soon|this|within|before)\b",
    r"\b(expected|projected|forecast(ed)?)\s+(annual\s+)?returns?\s+(of|is|are|at)\s*₹?\s*\d",
    r"\b(price\s+)?target\s*(price)?\s*(of|is|:)\s*₹?\s*\d",
    r"\b(nifty|sensex|bank\s*nifty|gold|bitcoin)\b[^.!?]{0,40}\b(will|to)\s+(reach|hit|cross|touch|fall\s+to|rise\s+to)\b",
    r"\byou\s+will\s+(earn|make|get|gain)\s+(a\s+)?(profit|₹|rs|\d)",
]
_OUT_REGULATORY = [
    r"\b(sebi|rbi|irdai|amfi|nse|bse|pfrda)\b[^.!?]{0,40}\b(says|said|states|stated|mandates|mandated|requires|required|has\s+(ruled|mandated|banned|approved|directed|decided)|guarantees|rules|prohibits|permits|allows|ensures)\b",
    r"\b(as\s+per|under|according\s+to)\s+(the\s+)?(sebi|rbi|irdai|amfi|income\s+tax|companies)\b[^.!?]{0,30}\b(act|rules?|regulations?|guidelines?|circular|law|section)\b",
    r"\bsection\s+\d+[a-z]?\s+of\s+the\b",
    r"\b(it\s+is|it's)\s+(legally|officially)\s+(required|mandatory|guaranteed|insured)\b",
    r"\b(deposits?|investments?|funds?)\s+(are|is)\s+(insured|guaranteed)\s+(up\s+to|by)\b",
]
_OUT_BROKER = re.compile(rf"\b({_BROKER_NAMES})\b", I)
_OUT_CRED_REQUEST = re.compile(r"\b(share|send|enter|tell|give|provide|type|read\s+out)\s+(me\s+|us\s+)?(your\s+|the\s+)?(otp|one[\s-]*time\s*(password|code)|upi\s*pin|atm\s*pin|pin|cvv|password|aadhaar|aadhar|pan(\s*card|\s*number)?|card\s*number)\b", I)


def _any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, I) for p in patterns)


@dataclass
class SafetyResult:
    allowed: bool
    categories: list[str] = field(default_factory=list)
    action: str = "allow"           # allow | block | rewrite | redact
    message: str | None = None      # safe educational response to show instead
    text: str = ""                  # text that may continue through the pipeline (sanitised)
    redactions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"allowed": self.allowed, "categories": self.categories, "action": self.action,
                "message": self.message, "redactions": self.redactions}


def check_input(text: str, lang: str = "en") -> SafetyResult:
    """Check what a user typed/said BEFORE any AI processing."""
    if text is None:
        text = ""
    text = text.strip()
    clean, kinds = redact(text)
    cats: list[str] = []
    norm = re.sub(r"\s+", " ", clean)
    if _any(_INJECTION_PATTERNS, norm):
        cats.append("injection")
    if _any(_REC_PATTERNS, norm):
        cats.append("recommendation")
    if _any(_BSH_PATTERNS, norm):
        cats.append("buy_sell_hold")
    if _any(_PRED_PATTERNS, norm):
        cats.append("prediction")
    if _any(_PERSONAL_PATTERNS, norm):
        cats.append("personalized")
    if _any(_BROKER_PATTERNS, norm):
        cats.append("broker_promotion")
    if kinds:
        cats.append("sensitive_data")
    if not cats:
        return SafetyResult(True, [], "allow", None, clean)
    # sensitive data alone: continue with the redacted text, but tell the user
    if cats == ["sensitive_data"]:
        return SafetyResult(True, cats, "redact", safe_response("sensitive_data", lang), clean, kinds)
    primary = ("injection" if "injection" in cats else "personalized" if "personalized" in cats else
               "broker_promotion" if "broker_promotion" in cats else "prediction" if "prediction" in cats else "recommendation")
    msg = safe_response(primary, lang)
    if "sensitive_data" in cats:
        msg = safe_response("sensitive_data", lang) + " " + msg
    return SafetyResult(False, cats, "block", msg, clean, kinds)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p for p in parts if p and p.strip()]


def check_output(text: str, lang: str = "en", cited: bool = False) -> SafetyResult:
    """Check generated text BEFORE it reaches the user. `cited=True` means it was built from retrieved,
    cited material, which permits regulatory statements that appear in that material."""
    if not text:
        return SafetyResult(True, [], "allow", None, "")
    cats: list[str] = []
    kept: list[str] = []
    bad = 0
    sents = _sentences(text)
    for s in sents:
        s_cats = []
        if _any(_OUT_ADVICE, s):
            s_cats.append("recommendation")
        if _any(_OUT_PREDICT, s):
            s_cats.append("prediction")
        if _OUT_BROKER.search(s):
            s_cats.append("broker_promotion")
        if _OUT_CRED_REQUEST.search(s) and not re.search(r"\b(never|don'?t|do\s+not|nahi|mat|kabhi\s+nahi|not\s+to|avoid)\b", s, I):
            s_cats.append("sensitive_data")
        if not cited and _any(_OUT_REGULATORY, s):
            s_cats.append("regulatory")
        if s_cats:
            bad += 1
            cats += s_cats
        else:
            kept.append(s)
    cats = sorted(set(cats))
    red_text, kinds = redact(" ".join(kept))
    if kinds:
        cats = sorted(set(cats + ["sensitive_data"]))
    if not cats:
        return SafetyResult(True, [], "allow", None, text)
    if not kept or bad >= max(2, len(sents) // 2 + 1):
        primary = cats[0]
        if "regulatory" in cats and len(cats) == 1:
            replacement = INSUFFICIENT.get(lang, INSUFFICIENT["en"])
        else:
            replacement = safe_response("recommendation" if primary in ("recommendation", "prediction", "broker_promotion") else
                                        "sensitive_data" if primary == "sensitive_data" else "regulatory", lang)
        return SafetyResult(False, cats, "rewrite", replacement, replacement, kinds)
    suffix = INSUFFICIENT.get(lang, INSUFFICIENT["en"]) if "regulatory" in cats else ""
    final = (red_text + (" " + suffix if suffix else "")).strip()
    return SafetyResult(False, cats, "rewrite", final, final, kinds)


def guard_text(text: str, lang: str = "en", cited: bool = False) -> str:
    """Convenience: return a text that is guaranteed to have passed the output check."""
    res = check_output(text, lang, cited)
    return res.text if res.action == "rewrite" else text
