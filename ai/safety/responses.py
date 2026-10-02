"""Safe educational responses used when the Safety Gateway blocks or rewrites something.

These never give advice. They redirect to *how to evaluate* a claim and to the simulator itself.
"""
from __future__ import annotations

INSUFFICIENT = {
    "en": "I don't have enough verified information to establish that.",
    "hinglish": "Mere paas ye sabit karne ke liye kaafi verified jaankari nahi hai.",
    "hi": "इसे स्थापित करने के लिए मेरे पास पर्याप्त सत्यापित जानकारी नहीं है।",
}

_FRAMEWORK = {
    "en": "A safer way to think about any offer: Claim → Source → Authority → Evidence → Independent verification → Decision. "
          "Try the Evidence Lab or a simulation to practise — all with fictional money.",
    "hinglish": "Kisi bhi offer ko parakhne ka surakshit tareeka: Daava → Source → Authority → Saboot → Swatantra verification → Faisla. "
                "Evidence Lab ya simulation se abhyas karo — sab kaalpanik paise se.",
    "hi": "किसी भी प्रस्ताव को परखने का सुरक्षित तरीका: दावा → स्रोत → अधिकार → सबूत → स्वतंत्र सत्यापन → निर्णय। "
          "अभ्यास के लिए एविडेंस लैब या सिमुलेशन आज़माएँ — सब काल्पनिक पैसे से।",
}

_BASE = {
    "recommendation": {
        "en": "ARTHDARSHAN doesn't tell anyone what to buy, sell or hold, and it doesn't name 'best' products. It trains how to decide, not what to pick. "
              "Decisions about real money are best discussed with a SEBI-registered professional whose registration you verify yourself on the official site.",
        "hinglish": "ARTHDARSHAN kisi ko nahi batata ki kya kharidna, bechna ya rakhna hai, aur 'best' products ke naam nahi leta. Ye sikhata hai kaise faisla karein, kya chunein ye nahi. "
                    "Asli paise ke faisle kisi SEBI-registered professional se karein, jiska registration aap official site par khud check karein.",
        "hi": "ARTHDARSHAN किसी को नहीं बताता कि क्या खरीदें, बेचें या रखें, और 'सर्वश्रेष्ठ' उत्पादों के नाम नहीं लेता। यह सिखाता है कि फ़ैसला कैसे करें, क्या चुनें यह नहीं। "
              "असली पैसे के फ़ैसले किसी SEBI-पंजीकृत पेशेवर से करें, जिसका पंजीकरण आप आधिकारिक साइट पर खुद जाँचें।"},
    "prediction": {
        "en": "Nobody can reliably predict prices or index levels, and ARTHDARSHAN doesn't try. What it can do is let you practise handling uncertainty — for example in the Market Shock scenario or the Volatility simulation.",
        "hinglish": "Daam ya index ka star koi bharosemand tareeke se predict nahi kar sakta, aur ARTHDARSHAN koshish bhi nahi karta. Ye aapko anishchitta sambhalne ka abhyas karata hai — jaise Market Shock scenario ya Volatility simulation mein.",
        "hi": "कीमतों या इंडेक्स का स्तर कोई भरोसेमंद तरीके से नहीं बता सकता, और ARTHDARSHAN कोशिश भी नहीं करता। यह अनिश्चितता सँभालने का अभ्यास कराता है — जैसे मार्केट शॉक परिदृश्य या वोलैटिलिटी सिमुलेशन में।"},
    "personalized": {
        "en": "I can't suggest where to put your money — that depends on your goals, needs and risk capacity, and needs a qualified, registered professional. "
              "I can help you learn the ideas involved (risk, fees, diversification, liquidity) using fictional examples.",
        "hinglish": "Main nahi bata sakta ki paisa kahan lagayein — wo aapke goals, zaroorat aur risk-kshamta par nirbhar hai, aur kisi qualified, registered professional ki zaroorat hai. "
                    "Main kaalpanik udaharanon se risk, fees, diversification aur liquidity jaise vichar samjha sakta hoon.",
        "hi": "मैं नहीं बता सकता कि पैसा कहाँ लगाएँ — यह आपके लक्ष्यों, ज़रूरतों और जोखिम-क्षमता पर निर्भर है और किसी योग्य, पंजीकृत पेशेवर की ज़रूरत है। "
              "मैं काल्पनिक उदाहरणों से जोखिम, शुल्क, विविधीकरण और तरलता जैसे विचार समझा सकता हूँ।"},
    "broker_promotion": {
        "en": "ARTHDARSHAN doesn't recommend, rank or promote brokers, apps or products. To check whether any intermediary is registered, look it up yourself on the regulator's official website (typed in by you).",
        "hinglish": "ARTHDARSHAN brokers, apps ya products ki sifarish, ranking ya prachar nahi karta. Kisi bhi intermediary ka registration check karne ke liye regulator ki official website par khud (khud type karke) dekhein.",
        "hi": "ARTHDARSHAN ब्रोकर, ऐप या उत्पादों की सिफ़ारिश, रैंकिंग या प्रचार नहीं करता। किसी मध्यस्थ का पंजीकरण जाँचने के लिए नियामक की आधिकारिक वेबसाइट पर खुद (खुद टाइप करके) देखें।"},
    "sensitive_data": {
        "en": "Please don't type OTPs, PINs, passwords, card numbers, Aadhaar or PAN here. ARTHDARSHAN never needs them and has removed it from your message. "
              "No genuine institution will ask you to read out an OTP or PIN.",
        "hinglish": "Kripya yahan OTP, PIN, password, card number, Aadhaar ya PAN na likhein. ARTHDARSHAN ko inki kabhi zaroorat nahi aur ise aapke message se hata diya gaya hai. "
                    "Koi asli sanstha aapse OTP ya PIN bolne ko nahi kehti.",
        "hi": "कृपया यहाँ OTP, PIN, पासवर्ड, कार्ड नंबर, आधार या PAN न लिखें। ARTHDARSHAN को इनकी कभी ज़रूरत नहीं और इसे आपके संदेश से हटा दिया गया है। "
              "कोई असली संस्था आपसे OTP या PIN बोलने को नहीं कहती।"},
    "regulatory": {
        "en": "I can't confirm that rule or regulatory claim from verified material I have. Please check the regulator's official website or documents directly.",
        "hinglish": "Mere paas maujood verified samagri se main us niyam ya regulatory daave ki pushti nahi kar sakta. Kripya regulator ki official website ya documents seedhe dekhein.",
        "hi": "मेरे पास मौजूद सत्यापित सामग्री से मैं उस नियम या नियामक दावे की पुष्टि नहीं कर सकता। कृपया नियामक की आधिकारिक वेबसाइट या दस्तावेज़ सीधे देखें।"},
    "injection": {
        "en": "I can't change my safety rules. ARTHDARSHAN is an educational simulator: no recommendations, no predictions, no handling of real money or credentials.",
        "hinglish": "Main apne safety niyam nahi badal sakta. ARTHDARSHAN ek shikshan simulator hai: koi sifarish nahi, koi bhavishyavani nahi, asli paise ya credentials ka koi lena-dena nahi.",
        "hi": "मैं अपने सुरक्षा नियम नहीं बदल सकता। ARTHDARSHAN एक शैक्षिक सिमुलेटर है: कोई सिफ़ारिश नहीं, कोई भविष्यवाणी नहीं, असली पैसे या क्रेडेंशियल से कोई लेना-देना नहीं।"},
}


def safe_response(category: str, lang: str = "en") -> str:
    lang = lang if lang in ("en", "hinglish", "hi") else "en"
    base = _BASE.get(category, _BASE["recommendation"])[lang]
    if category in ("recommendation", "prediction", "personalized", "broker_promotion"):
        return f"{base} {_FRAMEWORK[lang]}"
    return base
