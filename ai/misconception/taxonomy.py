"""Misconception taxonomy. M001–M012 are from the project brief; M013 is added (paperwork can wait).

Each entry carries: plain description, a non-judgemental correction (en/hinglish/hi), the related concept,
and regex `patterns` (English + Hinglish) used by the rule layer. Rules are high-precision, the ML layer adds recall.
"""
from __future__ import annotations

MISCONCEPTIONS: list[dict] = [
    {
        "id": "M001", "name": "Guaranteed-return misconception", "concept": "risk",
        "description": "Believing an investment can promise a fixed or risk-free high return.",
        "correction": {
            "en": "Market-linked investments cannot honestly guarantee returns. A promise of guaranteed high returns is a warning sign, not a reason to relax.",
            "hinglish": "Market se jude investments sach mein returns guarantee nahi kar sakte. Ooncha 'guaranteed' return ka vaada chetavani hai, tasalli nahi.",
            "hi": "बाज़ार से जुड़े निवेश रिटर्न की गारंटी नहीं दे सकते। ऊँचे 'गारंटीशुदा' रिटर्न का वादा चेतावनी है, तसल्ली नहीं।"},
        "patterns": [r"guarante\w*", r"gaurant\w*", r"pakka\s+(return|munafa|profit)", r"risk[\s-]*free", r"\bno\s+risk\b",
                     r"(sure|certain)\s+(profit|return|shot|gain)", r"100\s*%\s*(safe|secure)", r"fixed\s+(high\s+)?returns?",
                     r"\bzero\s+risk\b", r"surely\s+(earn|profit|make)", r"tay\s+(return|munafa)"],
        "needs_belief": [r"(so|therefore|hence|isliye|that'?s why|sounds|great|good|safe|best|trust|invest|take|join|lena|le lo|achha|accha|sahi|mil\w*|will (earn|get|make))"],
    },
    {
        "id": "M002", "name": "Social proof = legitimacy", "concept": "social_proof",
        "description": "Treating the fact that many people are involved as evidence that something is genuine.",
        "correction": {
            "en": "Other people's participation is not independent evidence of legitimacy. Crowds can be fooled, paid, or fake.",
            "hinglish": "Doosron ka judna legitimacy ka swatantra saboot nahi hai. Bheed ko bhi dhokha diya ja sakta hai, ya wo nakli ho sakti hai.",
            "hi": "दूसरों का जुड़ना असली होने का स्वतंत्र सबूत नहीं है। भीड़ को भी धोखा दिया जा सकता है, या वह नकली हो सकती है।"},
        "patterns": [r"(everyone|everybody|so many (people|members)|lots of people|many people|others (are|have)|240|sab\s+log|sabhi|bahut\s+log|log\s+(invest|kar rahe|jud))[^.!?]{0,70}(legit|safe|genuine|real|trust|fine|sahi|theek|asli|must be|probably|works)",
                     r"(legit|safe|genuine|real|sahi|theek|asli)[^.!?]{0,40}(because|since|as|kyunki|isliye)[^.!?]{0,40}(everyone|many|others|sab|group|members|log)",
                     r"(everyone|sab\s+log)\s+(is|are|hai|hain)?\s*(in|invest\w*|kar rahe)", r"so many (people|members)", r"\bsabhi\b[^.!?]{0,30}\bhain\b"],
    },
    {
        "id": "M003", "name": "Past performance = guaranteed future performance", "concept": "risk",
        "description": "Assuming that returns earned in the past will repeat.",
        "correction": {
            "en": "Past performance does not guarantee future results. Strong past numbers can be selected, edited, or simply not repeat.",
            "hinglish": "Pichla performance aage ke results ki guarantee nahi hai. Achhe purane numbers chune hue, edit kiye hue ya dobara na doharne wale ho sakte hain.",
            "hi": "पिछला प्रदर्शन भविष्य के नतीजों की गारंटी नहीं है। अच्छे पुराने आँकड़े चुने हुए या बदले हुए हो सकते हैं।"},
        "patterns": [r"(last|past|previous|pichhl\w*|pichl\w*)[^.!?]{0,40}(year|month|quarter|saal|mahine|returns?|performance|results?|record)[^.!?]{0,70}(so|therefore|will|again|isliye|aage|continue|repeat|same|similar|expect)",
                     r"track\s+record[^.!?]{0,40}(proves|means|shows|so)", r"(gave|earned|made)[^.!?]{0,30}\d+\s*%[^.!?]{0,40}(so|will|again|isliye)",
                     r"(it|they|fund)\s+(has\s+)?(always|consistently)\s+(gave|given|earned|performed)"],
    },
    {
        "id": "M004", "name": "Diversification eliminates all risk", "concept": "diversification",
        "description": "Believing that spreading money across several assets removes the possibility of loss.",
        "correction": {
            "en": "Diversification reduces concentration risk, but it cannot remove market-wide risk. Several assets can fall together.",
            "hinglish": "Diversification concentration risk ghatata hai, par poore market ke risk ko khatam nahi karta. Kai assets ek saath gir sakte hain.",
            "hi": "विविधीकरण एकाग्रता जोखिम घटाता है, पर पूरे बाज़ार का जोखिम ख़त्म नहीं करता। कई संपत्तियाँ एक साथ गिर सकती हैं।"},
        "patterns": [r"(diversif\w*|spread\w*|alag\s*alag|different (stocks|funds|assets)|many (stocks|funds))[^.!?]{0,70}(no risk|risk[\s-]*free|can'?t lose|cannot lose|zero risk|no loss|loss nahi|risk khatam|eliminat\w*|completely safe|totally safe|fully safe|safe from everything)",
                     r"(can'?t|cannot|won'?t)\s+lose[^.!?]{0,40}(spread|diversif|different)"],
    },
    {
        "id": "M005", "name": "Higher return = better opportunity", "concept": "risk",
        "description": "Assuming a higher promised return automatically means a better opportunity.",
        "correction": {
            "en": "A higher promised return usually comes with higher risk, or may be false. It does not make an opportunity better.",
            "hinglish": "Zyada vaada kiya gaya return aam taur par zyada risk ke saath aata hai, ya jhootha ho sakta hai. Isse opportunity behtar nahi ho jaati.",
            "hi": "ज़्यादा वादा किया गया रिटर्न आम तौर पर ज़्यादा जोखिम के साथ आता है, या झूठा हो सकता है। इससे अवसर बेहतर नहीं हो जाता।"},
        "patterns": [r"(higher|more|bigger|zyada|ooncha|high|30\s*%|85\s*%)[^.!?]{0,30}(returns?|munafa|profit)[^.!?]{0,40}(better|best|more attractive|achha|accha|behtar|worth|take it|go for|obvious)",
                     r"take\s+the\s+higher", r"sabse\s+zyada\s+(return|munafa|profit)", r"more\s+(profit|return)s?\s+means\s+better",
                     r"(why|kyun)\s+(would|will|should)\s+i\s+(take|choose|pick)\s+(less|lower|kam)"],
    },
    {
        "id": "M006", "name": "Urgency means the opportunity is disappearing", "concept": "fomo",
        "description": "Treating a deadline or 'limited slots' as a reason to act before checking.",
        "correction": {
            "en": "Urgency is a pressure tactic. Genuine, regulated products do not need a decision in minutes, and missing an unverified offer costs nothing.",
            "hinglish": "Jaldi ek dabaav ki chaal hai. Asli, regulated products ke liye minutes mein faisla nahi karna padta, aur unverified offer chhoot jaye to kuch nahi jaata.",
            "hi": "जल्दबाज़ी दबाव की चाल है। असली, विनियमित उत्पादों के लिए मिनटों में फ़ैसला नहीं करना पड़ता, और अनजाँचा प्रस्ताव छूटे तो कुछ नहीं जाता।"},
        "patterns": [r"(limited\s+(time|slots)|only\s+\d+\s+slots?|last\s+chance|slots?\s+(are\s+)?(ending|filling|left|over)|will\s+(be\s+)?(gone|disappear|expire|close)|miss\s+(out|the)|opportunity\s+(will\s+)?(go|end|vanish))[^.!?]{0,60}(so|must|should|have to|need to|better|quick\w*|immediately|now|jaldi|abhi|isliye)",
                     r"(so|isliye)\s+(i\s+)?(must|should|have to|need to|better)[^.!?]{0,20}(now|quick\w*|immediately|today|jaldi|abhi)",
                     r"(abhi\s+nahi\s+to|jaldi\s+nahi\s+kiya|mauka\s+(haath\s+se|chala))", r"don'?t\s+want\s+to\s+miss", r"dont\s+want\s+to\s+miss",
                     r"mauka\s+(nahi\s+)?(chhodna|jaane\s+dena)"],
    },
    {
        "id": "M007", "name": "Authority language = legitimacy", "concept": "verification",
        "description": "Treating words such as 'registered', 'certified' or 'official' as proof by themselves.",
        "correction": {
            "en": "A claim of registration or approval is only a claim until you check it yourself with the official source.",
            "hinglish": "Registration ya approval ka daava tab tak sirf daava hai jab tak aap khud official source se check na karo.",
            "hi": "पंजीकरण या मंज़ूरी का दावा तब तक सिर्फ़ दावा है जब तक आप आधिकारिक स्रोत से खुद न जाँचें।"},
        "patterns": [r"(sebi|rbi|government|regulated|registered|certified|certificate|official|approved|sarkari)[^.!?]{0,50}(so|therefore|hence|means|isliye|matlab)[^.!?]{0,40}(safe|legit|genuine|real|trust|sahi|asli)",
                     r"since\s+(it|they)\s+(is|are)\s+(sebi|registered|certified|regulated|approved)", r"(certificate|registration)\s+(looks?|seems?)\s+(real|genuine|official|fine|legit)",
                     r"(sebi|registered|certified)\s+(hai|hain|toh|to)\s+(safe|sahi|theek)"],
    },
    {
        "id": "M008", "name": "Complex terminology = credibility", "concept": "financial_disclosures",
        "description": "Assuming that something filled with technical jargon must be expert and trustworthy.",
        "correction": {
            "en": "Complicated words do not make a product credible. If you cannot understand it, ask for plain language before deciding.",
            "hinglish": "Mushkil shabdon se product bharosemand nahi ho jaata. Samajh na aaye to faisle se pehle saral bhasha mein samjhane ko kaho.",
            "hi": "कठिन शब्दों से उत्पाद भरोसेमंद नहीं हो जाता। समझ न आए तो फ़ैसले से पहले सरल भाषा में समझाने को कहें।"},
        "patterns": [r"(complicated|complex|technical|jargon|difficult\s+words|fancy|professional|english)[^.!?]{0,50}(so|must|means|therefore|isliye)[^.!?]{0,30}(good|credible|genuine|legit|expert|trust|sahi)",
                     r"(they|it)\s+sounds?\s+(smart|professional|expert|official|intelligent)", r"sounds?\s+(so\s+)?(smart|professional|expert)",
                     r"(bade|mushkil)\s+(shabd|words)[^.!?]{0,40}(expert|sahi|professional|asli)", r"must\s+know\s+what\s+they'?re\s+doing"],
    },
    {
        "id": "M009", "name": "Small initial amount = low risk", "concept": "risk",
        "description": "Believing a small first payment makes a scheme safe to try.",
        "correction": {
            "en": "A small amount limits the size of a loss, but it does not test whether something is genuine. Scams often let small tests succeed to build trust.",
            "hinglish": "Chhota amount nuksaan ka size ghatata hai, par ye nahi parakhta ki cheez asli hai. Scams aksar chhote test safal hone dete hain taaki bharosa bane.",
            "hi": "छोटी रकम नुकसान का आकार घटाती है, पर यह नहीं परखती कि चीज़ असली है। ठग अक्सर छोटे टेस्ट सफल होने देते हैं ताकि भरोसा बने।"},
        "patterns": [r"(small|little|tiny|thoda|chhota|only\s+₹?\s*\d+|just\s+₹?\s*\d+|bas\s+₹?\s*\d+)[^.!?]{0,50}(amount|investment|test|try|paisa|risk)[^.!?]{0,60}(so|won'?t|no risk|can'?t|safe|nothing|loss nahi|harm|theek|fine|low risk)",
                     r"(small|tiny|little)\s+amount[^.!?]{0,20}(safe|no harm|low risk|no risk|fine|okay|ok)", r"(just|only)\s+to\s+(test|try)",
                     r"(test|try)\s+(it\s+)?with\s+(a\s+)?(small|little|tiny)", r"thoda\s+sa\s+(try|test)", r"bas\s+test\s+ke\s+liye"],
    },
    {
        "id": "M010", "name": "Losses must be recovered immediately", "concept": "risk",
        "description": "Feeling that a loss must be won back quickly, even by taking more risk or paying more.",
        "correction": {
            "en": "Money already paid or lost is gone either way. Paying or risking more to 'get it back' is how scams and bad decisions escalate.",
            "hinglish": "Jo paisa de diya ya kho diya wo dono taraf gaya hi hai. Wapas paane ke liye aur dena ya aur risk lena hi scams aur galat faislon ko badhata hai.",
            "hi": "जो पैसा दे दिया या खो दिया वह दोनों तरफ़ गया ही है। वापस पाने के लिए और देना या और जोखिम लेना ही ठगी और गलत फ़ैसलों को बढ़ाता है।"},
        "patterns": [r"(recover|win\s+back|make\s+up\s+for|break\s+even|get\s+(my|the)\s+(money|loss)\s+back|wapas\s+(paane|lene|kamane|mil)|nuksaan\s+(pura|recover|wapas)|loss\s+(wapas|recover|cover))",
                     r"already\s+(paid|lost|put|invested)[^.!?]{0,40}(so|more|again|can'?t stop|have to|might as well|zaruri|isliye)", r"average\s+down", r"double\s+down",
                     r"(one|ek)\s+(more|aur)\s+(time|baar|payment)[^.!?]{0,30}(then|phir|and|to)", r"come\s+this\s+far", r"itna\s+aage\s+aa"],
    },
    {
        "id": "M011", "name": "A friend's recommendation is sufficient evidence", "concept": "social_proof",
        "description": "Treating a trusted person's recommendation as proof that something is safe.",
        "correction": {
            "en": "A friend can be sincere and still be wrong or fooled. Ask what independent evidence exists beyond their word.",
            "hinglish": "Dost sachcha hokar bhi galat ya dhokhe mein ho sakta hai. Poochho unke kehne ke alawa swatantra saboot kya hai.",
            "hi": "दोस्त सच्चा होकर भी गलत या धोखे में हो सकता है। पूछें कि उनके कहने के अलावा स्वतंत्र सबूत क्या है।"},
        "patterns": [r"(my\s+)?(friend|cousin|brother|sister|colleague|dost|bhai|rishtedar|uncle|aunt|neha|relative|boss)[^.!?]{0,60}(told|said|invested|recommend\w*|suggest\w*|bataya|kaha|lagaya|made|earned)[^.!?]{0,60}(so|therefore|isliye|must be|probably|sure|legit|safe|theek|trust|sahi|fine)",
                     r"(trust|believe)\s+(my\s+)?(friend|cousin|brother|dost|bhai|neha|him|her)", r"dost\s+(ne\s+kaha|par\s+bharosa|hai\s+to)",
                     r"(she|he|they)'?s?\s+(my\s+)?(friend|family)[^.!?]{0,30}(so|would not|wouldn'?t|won'?t)\s*(lie|cheat|fool)", r"friend\s+(is|are)\s+in[^.!?]{0,30}(so|then)"],
    },
    {
        "id": "M012", "name": "Fees do not materially affect outcomes", "concept": "fees",
        "description": "Assuming small-looking percentage charges barely change the final amount.",
        "correction": {
            "en": "Fees compound over time. A charge that looks small each year can take a large share of the final amount.",
            "hinglish": "Fees samay ke saath jud kar badhti hain. Har saal chhoti dikhne wali fee ant mein bade hisse ko kha sakti hai.",
            "hi": "शुल्क समय के साथ जुड़कर बढ़ते हैं। हर साल छोटा दिखने वाला शुल्क अंत में बड़ा हिस्सा खा सकता है।"},
        "patterns": [r"(fee|charge|expense|commission|load|kharcha|shulk)s?[^.!?]{0,40}(small|tiny|only|just|nothing|negligible|not matter|don'?t matter|kuch nahi|bahut kam|chhota|1\s*%|2\s*%|2\.5\s*%)[^.!?]{0,40}(so|ignore|doesn'?t|won'?t|no big|fark nahi|matter nahi|fine|ok|okay)",
                     r"\b(1|2|2\.5|3)\s*%[^.!?]{0,30}(is\s+)?(nothing|small|tiny|not much|kuch nahi|negligible)", r"fees?\s+(don'?t|doesn'?t|do not|does not)\s+(matter|affect|change)",
                     r"fees?\s+se\s+(kuch\s+)?(fark|farak)\s+nahi", r"(only|just)\s+\d(\.\d)?\s*%\s+(fee|charge)", r"roughly\s+the\s+same"],
    },
    {
        "id": "M013", "name": "Paperwork and nomination can wait", "concept": "nomination",
        "description": "Postponing nominations, records and documents until something happens.",
        "correction": {
            "en": "Preparedness works only if it is done before it is needed. Updated nominations and a simple list of accounts spare families confusion later.",
            "hinglish": "Taiyaari tabhi kaam aati hai jab zaroorat se pehle ki jaye. Updated nomination aur accounts ki simple list baad mein parivaar ko uljhan se bachati hai.",
            "hi": "तैयारी तभी काम आती है जब ज़रूरत से पहले की जाए। अद्यतन नामांकन और खातों की सरल सूची बाद में परिवार को उलझन से बचाती है।"},
        "patterns": [r"(nominee|nomination|document\w*|paperwork|kaagaz|will|records?)[^.!?]{0,60}(later|baad\s+mein|not\s+needed|zaroori\s+nahi|no\s+need|can\s+wait|abhi\s+nahi|when\s+needed|zarurat\s+padne)",
                     r"(later|baad\s+mein|when\s+needed|if\s+something\s+happens|zarurat\s+padne\s+par|abhi\s+kya\s+jaldi)[^.!?]{0,40}(nominee|nomination|document|paperwork|kaagaz|will|records?)", r"no\s+hurry"],
    },
]

MISCONCEPTION_IDS = [m["id"] for m in MISCONCEPTIONS]
BY_ID = {m["id"]: m for m in MISCONCEPTIONS}

# A sentence expressing doubt/scepticism is not evidence of the misconception it mentions.
SKEPTIC = (r"(scam|fraud|fake|suspicious|red\s*flag|not\s+(a\s+)?(proof|evidence|enough|guarantee\w*|independent)|doesn'?t\s+(prove|mean)|"
           r"can'?t\s+be\s+(true|guaranteed)|cannot\s+be\s+(true|guaranteed)|no\s+one\s+can|nobody\s+can|shak|dhokha|thagi|nakli|doubt|"
           r"verify|check\s+(it\s+)?first|isn'?t\s+(proof|evidence)|nahi\s+(hota|ho\s+sakta)|saboot\s+nahi|too\s+good|warning|why\s+would|"
           r"not\s+a\s+reason|not\s+safe|not\s+genuine|not\s+real|nahi\s+(hai|hota)|myth|wrong|galat)")
