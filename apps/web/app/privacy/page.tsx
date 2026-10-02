"use client";
import Link from "next/link";
import { PageHead } from "@/components/ui";
import { useApp } from "@/lib/state";

export default function Privacy() {
  const { t, lang } = useApp();
  const tx = (en: string, hing: string, hi: string) => (lang === "en" ? en : lang === "hi" ? hi : hing);
  const stored: [string, string, string][] = [
    ["A random profile token (stored in your browser) and an optional display name you choose.", "Ek random profile token (aapke browser mein) aur ek optional display name jo aap chunte ho.", "एक रैंडम प्रोफ़ाइल टोकन (आपके ब्राउज़र में) और एक वैकल्पिक डिस्प्ले नाम जो आप चुनें।"],
    ["Each decision: which action, how long it took, your confidence, which warning signs you marked, and the reasoning text you typed or spoke (with any sensitive-looking numbers masked before saving).", "Har faisla: kaun sa kadam, kitna samay laga, aapka vishwas, kaun se chetavani sanket aapne chune, aur aapka likha ya bola gaya tark (sensitive dikhne wale number save hone se pehle chhupa diye jaate hain).", "हर फ़ैसला: कौन सा कदम, कितना समय लगा, आपका विश्वास, कौन से चेतावनी संकेत आपने चुने, और आपका लिखा या बोला तर्क (संवेदनशील दिखने वाले नंबर सहेजने से पहले छिपा दिए जाते हैं)।"],
    ["Derived learning data: fingerprint scores, concept mastery, detected misconceptions and quiz answers.", "Nikala gaya seekhne ka data: fingerprint score, concept mastery, pehchani galatfehmiyan aur quiz ke jawab.", "निकाला गया सीखने का डेटा: फ़िंगरप्रिंट स्कोर, अवधारणा पकड़, पहचानी गलतफ़हमियाँ और क्विज़ के जवाब।"],
    ["Simulation settings you tried (fictional numbers only).", "Aapke try kiye simulation settings (sirf kaalpanik number).", "आपके आज़माए सिमुलेशन सेटिंग्स (सिर्फ़ काल्पनिक संख्याएँ)।"],
  ];
  const never: [string, string, string][] = [
    ["OTPs, PINs, passwords, card numbers, Aadhaar, PAN, bank or brokerage details — the app never asks for them and the safety gateway masks them if typed.", "OTP, PIN, password, card number, Aadhaar, PAN, bank ya brokerage vivaran — app kabhi nahi maangta aur type karne par safety gateway unhe chhupa deta hai.", "OTP, PIN, पासवर्ड, कार्ड नंबर, आधार, PAN, बैंक या ब्रोकरेज विवरण — ऐप कभी नहीं माँगता और टाइप करने पर सुरक्षा गेटवे उन्हें छिपा देता है।"],
    ["Email, phone number, address, real name or location.", "Email, phone number, pata, asli naam ya location.", "ईमेल, फ़ोन नंबर, पता, असली नाम या स्थान।"],
    ["Any data sent to an outside service: all AI (language model, speech, retrieval) runs on this machine. No analytics or tracking.", "Kisi bahari service ko koi data nahi bheja jaata: saara AI (language model, speech, retrieval) is machine par chalta hai. Koi analytics ya tracking nahi.", "किसी बाहरी सेवा को कोई डेटा नहीं भेजा जाता: सारा AI (भाषा मॉडल, वाणी, खोज) इसी मशीन पर चलता है। कोई एनालिटिक्स या ट्रैकिंग नहीं।"],
  ];
  return (
    <article className="max-w-3xl space-y-6">
      <PageHead eyebrow={t("privacy")} title={t("privacy_page")} sub={tx("Short version: it stays on this device, and you can erase it in one tap.", "Seedhi baat: sab kuch is device par rehta hai, aur aap ek tap mein mita sakte ho.", "सीधी बात: सब कुछ इस डिवाइस पर रहता है, और आप एक टैप में मिटा सकते हैं।")} />
      <section className="card p-5"><h2 className="text-xl font-bold text-midnight">{tx("What is stored (locally, in a SQLite file on this machine)", "Kya store hota hai (local, is machine ki SQLite file mein)", "क्या सहेजा जाता है (स्थानीय, इस मशीन की SQLite फ़ाइल में)")}</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5">{stored.map((s, i) => <li key={i}>{tx(...s)}</li>)}</ul></section>
      <section className="card p-5"><h2 className="text-xl font-bold text-maroon">{tx("What is never collected", "Kya kabhi collect nahi hota", "क्या कभी इकट्ठा नहीं होता")}</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5">{never.map((s, i) => <li key={i}>{tx(...s)}</li>)}</ul></section>
      <section className="card p-5"><h2 className="text-xl font-bold text-midnight">{tx("Your controls", "Aapke control", "आपके नियंत्रण")}</h2>
        <p className="mt-2">{tx("In Settings you can download everything stored about you, delete all learning data, or delete the profile completely. Deletion is immediate and permanent.", "Settings mein aap apne baare mein store sab kuch download kar sakte ho, saara seekhne ka data hata sakte ho, ya profile poora hata sakte ho. Hatana turant aur sthayi hai.", "सेटिंग्स में आप अपने बारे में सहेजा सब कुछ डाउनलोड कर सकते हैं, सारा सीखने का डेटा हटा सकते हैं, या प्रोफ़ाइल पूरी तरह हटा सकते हैं। हटाना तुरंत और स्थायी है।")}</p>
        <Link href="/settings" className="btn-night mt-4">{t("nav_settings")}</Link></section>
    </article>
  );
}
