from _lib import A, CH, E, END, L, P, ST, scenario

# All numbers are ILLUSTRATIVE, computed here so text matches the simulator exactly.
AMOUNT = 100_000
GROSS = 0.08


def plan_value(entry: float, yearly: float, years: int) -> int:
    v = AMOUNT * (1 - entry)
    for _ in range(years):
        v = v * (1 + GROSS) * (1 - yearly)
    return round(v)


A5, B5 = plan_value(0.03, 0.025, 5), plan_value(0.0, 0.005, 5)
A20, B20 = plan_value(0.03, 0.025, 20), plan_value(0.0, 0.005, 20)
F = lambda n: f"₹{n:,}"  # noqa: E731

SC = scenario(
    id="hidden_fee",
    title=L("The Hidden Fee", "The Hidden Fee (Chhupi Hui Fee)"),
    tagline=L("A brochure shouts 'up to 10%'. The charges are in small print.", "Brochure chillata hai 'up to 10%'. Charges chhoti likhai mein hain."),
    character={"name": "Farida", "age": 31, "role": "shop owner reading a brochure (fictional)"},
    difficulty=2,
    concept_tags=["fees", "financial_disclosures", "compounding", "mutual_fund"],
    pressure_tags=["urgency", "authority"],
    tests=["M012", "M005", "M008"],
    initial="f1_brochure",
    dimensions=["concept_knowledge", "terminology", "evidence_verification"],
    states=[
        ST("f1_brochure", L("The brochure", "Brochure"),
           L("An agent gives Farida a brochure for the fictional 'Sunrise Wealth Plan'. The headline is large; other lines are small.",
             "Ek agent Farida ko kaalpanik 'Sunrise Wealth Plan' ka brochure deta hai. Headline bada hai; baaki lines chhoti."),
           channel=CH("document", "Sunrise Wealth Plan brochure (fictional)", [
               L("Illustration: up to 10% growth per year*", "Illustration: saal mein up to 10% growth*"),
               L("Only a small admin charge.", "Sirf ek chhota admin charge."),
               L("Sign today and receive a free gift.", "Aaj sign karo aur free gift pao."),
               L("*Illustrative, not guaranteed. Charges apply — see page 14.", "*Illustrative, guaranteed nahi. Charges lagu — page 14 dekho.")]),
           pressure=[P("urgency", L("“Sign today for a free gift.”", "“Aaj sign karo free gift ke liye.”")), P("authority", L("A confident, helpful agent.", "Ek aatmavishwasi, madadgaar agent."))],
           evidence=[
               E("fb_head", L("“Up to 10% a year” in large print", "“Saal mein up to 10%” bade akshron mein"), L("The biggest number is the best case.", "Sabse bada number sabse achha case hai."), "red_flag",
                 L("'Up to' describes a ceiling, not what you will get. Marketing leads with the best-looking figure.", "'Up to' sheersh seema hai, jo aapko milega wo nahi. Marketing sabse achhe dikhne wale figure se shuru karti hai."), "headline_figure"),
               E("fb_admin", L("“Only a small admin charge” — no number given", "“Sirf chhota admin charge” — koi number nahi"), L("The size of the charge is not stated.", "Charge ka size nahi bataya."), "red_flag",
                 L("A cost described as 'small' without a number cannot be compared. Ask for it in rupees and percentages.", "Bina number ke 'chhota' kahe gaye kharche ki tulna nahi ho sakti. Use rupees aur percentage mein poochho."), "missing_disclosure"),
               E("fb_gift", L("Free gift for signing today", "Aaj sign karne par free gift"), L("A reason to decide quickly.", "Jaldi faisla karne ki wajah."), "red_flag",
                 L("Rewards for deciding today work against careful reading of the charges.", "Aaj faisla karne ke inaam charges ko dhyan se padhne ke khilaf kaam karte hain."), "urgency"),
               E("fb_note", L("“Not guaranteed. Charges apply — see page 14.”", "“Guaranteed nahi. Charges lagu — page 14 dekho.”"), L("The important facts are in the small footnote.", "Zaroori baatein chhote footnote mein hain."), "neutral",
                 L("Good news: the footnote tells you where to look. Read the footnotes first.", "Achhi baat: footnote batata hai kahan dekhna hai. Footnote pehle padho."))],
           actions=[
               A("sign_now", L("Sign today — 10% sounds great and the charge is 'small'", "Aaj hi sign karo — 10% achha hai aur charge 'chhota' hai"), "unsafe", "t_surprise",
                 L("You sign. Months later the statement shows deductions you never calculated.", "Aap sign karte ho. Mahino baad statement mein aise kate hue paise dikhte hain jinka hisaab aapne nahi lagaya."), verification=False, misconception_signals=["M012", "M005"]),
               A("ask_charges", L("Ask for every charge in rupees and percentages, in writing", "Har charge rupees aur percentage mein, likhit mein maango"), "safe", "f2_charges",
                 L("The agent hands over the charges table on page 14.", "Agent page 14 ka charges table deta hai."), verification=True, requests_evidence=True),
               A("take_home", L("Take it home and read the footnotes before deciding", "Ghar le jao aur faisle se pehle footnotes padho"), "safe", "f2_charges",
                 L("The gift offer lapses; the charges table is on page 14.", "Gift offer khatam hota hai; charges table page 14 par hai."), verification=True, requests_evidence=True),
               A("compare_headlines", L("Compare this plan's 10% with another plan's 'up to 9%'", "Is plan ke 10% ki doosre plan ke 'up to 9%' se tulna karo"), "unsafe", "f2_charges",
                 L("You compare two best-case numbers. Neither shows what you would keep.", "Aap do best-case number ki tulna karte ho. Koi bhi nahi dikhata ki aap kitna rakhoge."), misconception_signals=["M005"])],
           reasoning_prompt=L("What do you want to know before deciding?", "Faisle se pehle aap kya jaanna chahte ho?")),
        ST("f2_charges", L("Page 14: the charges", "Page 14: charges"),
           L("The charges are on page 14 (fictional). Plan A is the 'Sunrise Wealth Plan'. Plan B is a different, lower-cost fictional plan.",
             "Charges page 14 par hain (kaalpanik). Plan A 'Sunrise Wealth Plan' hai. Plan B ek doosra, kam kharche wala kaalpanik plan hai."),
           channel=CH("document", "Charges table (fictional)", [
               L("Plan A — Entry charge: 3% of amount. Yearly charge: 2.5% of fund value. Exit charge: 4% if you leave in the first 5 years.", "Plan A — Entry charge: rakam ka 3%. Yearly charge: fund value ka 2.5%. Exit charge: pehle 5 saal mein nikalne par 4%."),
               L("Plan B — Entry charge: 0%. Yearly charge: 0.5% of fund value. Exit charge: 1% if you leave in the first year.", "Plan B — Entry charge: 0%. Yearly charge: fund value ka 0.5%. Exit charge: pehle saal mein nikalne par 1%.")]),
           evidence=[
               E("c_year", L("A 2.5% charge every year, on a growing balance", "Har saal 2.5% charge, badhte balance par"), L("It repeats every year.", "Ye har saal dohrata hai."), "red_flag",
                 L("A yearly charge compounds against you: it is taken from a balance that is supposed to be growing.", "Yearly charge aapke khilaf compound hota hai: ye us balance se kata jaata hai jo badhna chahiye."), "annual_fee"),
               E("c_entry", L("A 3% entry charge reduces the amount that is invested", "3% entry charge nivesh hone wali rakam ghatata hai"), L("₹1,00,000 becomes ₹97,000 on day one.", "₹1,00,000 pehle din ₹97,000 ho jaata hai."), "red_flag",
                 L("Entry charges come off the top before any growth begins.", "Entry charge growth shuru hone se pehle hi upar se kat jaate hain."), "entry_load"),
               E("c_exit", L("A 4% exit charge in the first five years", "Pehle paanch saal mein 4% exit charge"), L("Leaving early costs extra.", "Jaldi nikalna mehnga padta hai."), "red_flag",
                 L("This links to liquidity: needing your money early would cost a further 4%.", "Ye liquidity se judta hai: paise jaldi chahiye to aur 4% lagega."), "exit_load"),
               E("c_b", L("Plan B shows much lower charges", "Plan B ke charges bahut kam hain"), L("0% entry, 0.5% yearly, 1% exit in year one.", "0% entry, 0.5% yearly, pehle saal 1% exit."), "neutral",
                 L("Lower charges are only one factor. They do not guarantee better returns, but they remove a certain drag.", "Kam charges sirf ek karak hain. Ye behtar returns ki guarantee nahi, par ek pakka bojh hatate hain."))],
           actions=[
               A("calc_net", L("Estimate net outcomes with the fee simulator, using one hypothetical growth rate for both plans", "Fee simulator se net nateeje nikalo, dono plans ke liye ek hi hypothetical growth rate ke saath"), "safe", "f3_compare",
                 L("You test both plans on equal assumptions.", "Aap dono plans ko ek jaisi manyataon par parakhte ho."), verification=True, requests_evidence=True,
                 observations=[{"dimension": "concept_knowledge", "value": 90}]),
               A("ignore_fee", L("2.5% looks small — I'll ignore the charges and look at growth", "2.5% chhota lagta hai — charges ignore karke growth dekhungi"), "unsafe", "f3_compare",
                 L("You set the charges aside and focus on the headline growth.", "Aap charges ko alag rakhkar headline growth par dhyan dete ho."), misconception_signals=["M012"],
                 observations=[{"dimension": "concept_knowledge", "value": 15}]),
               A("pick_headline", L("Pick whichever plan shows the higher 'up to' growth", "Jis plan ka 'up to' growth zyada ho wo chuno"), "unsafe", "f3_compare",
                 L("You choose by the best-case number.", "Aap best-case number se chunte ho."), misconception_signals=["M005"],
                 observations=[{"dimension": "concept_knowledge", "value": 20}]),
               A("ask_which_earns", L("Ask the agent which plan will earn more", "Agent se poochho kaun sa plan zyada kamayega"), "mixed", "f3_compare",
                 L("The agent smiles: “Mine, of course!” Nobody can honestly know future returns.", "Agent muskurata hai: “Mera, zaahir hai!” Bhavishya ke returns koi imaandaari se nahi jaan sakta."),
                 observations=[{"dimension": "concept_knowledge", "value": 45}])],
           reasoning_prompt=L("How do you think the charges change the final amount?", "Aapko kya lagta hai charges antim rakam ko kaise badalte hain?"), simulation_hint="fee_erosion"),
        ST("f3_compare", L("Same growth, different charges", "Ek jaisi growth, alag charges"),
           L(f"Using the same hypothetical 8% gross growth for both plans (illustrative — real growth varies and can be negative, but charges apply either way), ₹1,00,000 would become about {F(A5)} in Plan A and {F(B5)} in Plan B after 5 years; "
             f"after 20 years about {F(A20)} versus {F(B20)}. That is a gap of {F(B5 - A5)} after 5 years and {F(B20 - A20)} after 20 years from charges alone.",
             f"Dono plans ke liye ek hi hypothetical 8% gross growth lene par (illustrative — asli growth badalti hai aur negative bhi ho sakti hai, par charges dono haal mein lagte hain), ₹1,00,000 5 saal baad Plan A mein lagbhag {F(A5)} aur Plan B mein {F(B5)} hoga; "
             f"20 saal baad lagbhag {F(A20)} versus {F(B20)}. Sirf charges se 5 saal mein {F(B5 - A5)} aur 20 saal mein {F(B20 - A20)} ka fark."),
           channel=CH("document", "ILLUSTRATIVE · SIMULATED · NO REAL MONEY", [L("Hypothetical gross growth: 8% per year for both plans", "Dono plans ke liye hypothetical gross growth: 8% prati varsh")]),
           evidence=[
               E("g_gap", L(f"A gap of {F(B5 - A5)} after 5 years", f"5 saal mein {F(B5 - A5)} ka fark"), L("Same assumed growth, different charges.", "Maani hui growth ek jaisi, charges alag."), "neutral",
                 L("The gap comes only from charges. This is why 'small' percentages matter over time.", "Fark sirf charges se aata hai. Isi liye samay ke saath 'chhote' percentage bhi maayne rakhte hain.")),
               E("g_hyp", L("8% is hypothetical", "8% hypothetical hai"), L("Real results vary and can be negative.", "Asli nateeje badalte hain aur negative ho sakte hain."), "neutral",
                 L("Charges apply even in years when growth is poor. This simulation illustrates charges, it does not forecast returns.", "Kharab growth wale saalon mein bhi charges lagte hain. Ye simulation charges dikhata hai, returns ki bhavishyavani nahi.")),
               E("g_exit", L("Leaving Plan A early costs a further 4%", "Plan A jaldi chhodne par aur 4%"), L("It also reduces flexibility.", "Ye lachilapan bhi ghatata hai."), "red_flag",
                 L("An exit charge is a price on changing your mind or needing money.", "Exit charge apna mann badalne ya paise ki zaroorat par laga daam hai."), "exit_load")],
           actions=[
               A("ask_docs", L("Ask for the official key-facts document and all charges in writing, and decide only when I can explain them myself", "Official key-facts document aur saare charges likhit mein maango, aur tabhi faisla karo jab khud samjha sako"), "safe", "t_informed",
                 L("You collect the documents and read them at home.", "Aap documents jama karte ho aur ghar par padhte ho."), verification=True),
               A("lower_fee_guarantee", L("Choose the lower-charge plan because lower charges mean better returns", "Kam charge wala plan chuno kyunki kam charge matlab behtar returns"), "mixed", "t_partial",
                 L("Lower charges help, but they do not guarantee anything about returns.", "Kam charges madad karte hain, par returns ki koi guarantee nahi.")),
               A("friendly_agent", L("Choose the plan whose agent seems friendliest", "Jis plan ka agent sabse dostana lage wo chuno"), "unsafe", "t_surprise",
                 L("You decide on a feeling about a person rather than the numbers.", "Aap numbers ki jagah ek insaan ke ehsaas par faisla karte ho."), misconception_signals=["M008"]),
               A("take_gift", L("Take the free gift and sign Plan A", "Free gift lo aur Plan A sign karo"), "unsafe", "t_surprise",
                 L("You trade a gift for a long list of charges.", "Aap gift ke badle charges ki lambi list lete ho."), misconception_signals=["M012"])],
           reasoning_prompt=L("What is your decision process now?", "Ab aapka faisla lene ka tareeka kya hai?"), simulation_hint="fee_erosion"),
        END("t_informed", "safe", L("You made the charges visible", "Aapne charges ko saamne rakha"), L("You asked for every cost in writing and compared plans on equal assumptions. Decisions made after seeing the costs are different decisions.", "Aapne har kharche ko likhit mein maanga aur plans ko ek jaisi manyataon par tola. Kharche dekhne ke baad liye faisle alag hote hain.")),
        END("t_partial", "mixed", L("A good instinct, with a gap", "Achha anuman, ek kami ke saath"), L("Looking at charges is wise. But lower charges do not guarantee better returns, and other factors — risk, flexibility, goals — still matter. Ask for the key-facts document.", "Charges dekhna samajhdari hai. Par kam charges behtar returns ki guarantee nahi, aur risk, lachilapan, goals jaise karak bhi maayne rakhte hain. Key-facts document maango.")),
        END("t_surprise", "unsafe", L("The charges arrived later", "Charges baad mein aaye"), L(f"Without checking charges, the illustration looked better than the net result. In the simulation with 8% growth, 20 years of Plan A charges cost about {F(B20 - A20)} compared with Plan B (illustrative, simulated).", f"Charges dekhe bina illustration net nateeje se behtar dikha. 8% growth wale simulation mein Plan A ke 20 saal ke charges Plan B ke mukable lagbhag {F(B20 - A20)} mehnge pade (illustrative, simulated)."), loss=B20 - A20),
    ],
    reflection={
        "key_points": [
            L("Headline growth is a best case. Net outcome = growth minus every cost.", "Headline growth best case hai. Net nateeja = growth minus har kharcha."),
            L("A yearly charge compounds: over decades even small percentages take a large share.", "Yearly charge compound hota hai: dashakon mein chhote percentage bhi bada hissa le jaate hain."),
            L("Ask for all charges in rupees, in writing, and read the footnotes first.", "Saare charges rupees mein, likhit mein maango, aur footnote pehle padho."),
            L("Low charges do not guarantee good results — they just remove a certain drag.", "Kam charges achhe nateeje ki guarantee nahi — ye bas ek pakka bojh hatate hain.")],
        "questions": [L("What cost would you ask about first?", "Sabse pehle kis kharche ke baare mein poochhoge?")],
        "micro_lesson": {"concept_id": "fees", "title": L("Read the charges before the headline", "Headline se pehle charges padho"),
                         "body": L("Three questions: What is every charge in rupees? When is each charge taken (once or every year)? What does it cost to leave early? Then compare options on the same assumptions.",
                                   "Teen sawaal: Har charge rupees mein kitna? Har charge kab kata jaata hai (ek baar ya har saal)? Jaldi nikalne par kitna lagta hai? Phir options ki ek jaisi manyataon par tulna karo.")},
    },
)
