from _lib import A, CH, E, END, L, P, ST, scenario

# Fictional assets and numbers; all arithmetic below is computed (not typed) so the story is internally consistent.
TOTAL = 50_000
SHOCK = {"kaveri": -0.35, "brahmaputra": -0.32, "gomti": 0.02, "narmada": -0.03, "sutlej": 0.01}


def _fmt(n: float) -> str:
    return f"₹{abs(round(n)):,}"


def _event(alloc: dict[str, float]) -> tuple[int, int]:
    pnl = sum(v * SHOCK[k] for k, v in alloc.items())
    return round(pnl), round(TOTAL + pnl)


A_ALL = {"kaveri": 50_000}
A_SPLIT = {"kaveri": 12_500, "gomti": 12_500, "narmada": 12_500, "sutlej": 12_500}
A_SIM = {"kaveri": 25_000, "brahmaputra": 25_000}
A_BUF = {"kaveri": 10_000, "gomti": 10_000, "narmada": 10_000, "sutlej": 10_000}  # + 10,000 cash

shock_text = {
    "all": _event(A_ALL), "split": _event(A_SPLIT), "sim": _event(A_SIM), "buf": _event(A_BUF),
}


def after_event(key: str, en: str, hing: str) -> ST:
    pnl, total = shock_text[key]
    return ST(f"b2_{key}", L("The policy shock", "Policy ka jhatka"),
              L(f"A fictional government delays a solar subsidy. Kaveri Solar falls 35% and Brahmaputra Solar falls 32%; Gomti Foods +2%, Narmada Steel −3%, Sutlej Bank +1%. {en} "
                f"Your simulated ₹50,000 is now about {_fmt(total)} ({'−' if pnl < 0 else '+'}{_fmt(pnl)}).",
                f"Ek kaalpanik sarkar solar subsidy rok deti hai. Kaveri Solar 35% aur Brahmaputra Solar 32% girte hain; Gomti Foods +2%, Narmada Steel −3%, Sutlej Bank +1%. {hing} "
                f"Aapke simulated ₹50,000 ab lagbhag {_fmt(total)} hain ({'−' if pnl < 0 else '+'}{_fmt(pnl)})."),
              channel=CH("news", "Fictional business news", [L("SOLAR SHOCK: subsidy delayed. Sector falls sharply.", "SOLAR SHOCK: subsidy ruki. Sector tezi se gira.")]),
              pressure=[P("fear", L("Headlines say 'solar is finished'.", "Headlines kehti hain 'solar khatam'."))],
              evidence=[E("b2_conc", L("How much of your money depended on solar?", "Aapka kitna paisa solar par tika tha?"),
                          L("Compare how much each choice lost to the same event.", "Dekho ek hi ghatna se har choice ne kitna khoya."), "neutral",
                          L("The same event hurts very differently depending on how concentrated the money was.", "Ek hi ghatna se nuksaan is baat par nirbhar karta hai ki paisa kitna ek jagah tha.")),
                        E("b2_hold", L("“It will bounce back” — said with full certainty", "“Ye wapas aayega” — poore vishwas se kaha gaya"), L("Someone is sure about the future.", "Koi bhavishya ke baare mein pakka hai."), "red_flag",
                          L("Nobody knows. Certainty about recovery is as unreliable as certainty about collapse.", "Koi nahi jaanta. Sudhaar ka pakka vishwas utna hi bharosemand nahi jitna girne ka."), "overconfidence")],
              actions=[
                  A("review", L("Review: how much of my money depended on one company or sector?", "Review: mera kitna paisa ek company ya sector par tika tha?"), "safe", "b3_broad",
                    L("You list each holding and how it behaved. The picture is clearer.", "Aap har holding aur uske vyavhaar ki list banate ho. Tasveer saaf hoti hai."), verification=True),
                  A("double_down", L("Put the rest into the same company to win it back faster", "Baaki paisa usi company mein daalo taaki jaldi wapas aaye"), "unsafe", "t_doubled_down",
                    L("You increase the concentration right after seeing its effect.", "Aap asar dekhne ke turant baad concentration badha dete ho."), misconception_signals=["M010"]),
                  A("wait_sure", L("Do nothing; it's temporary, I'm sure", "Kuch mat karo; ye asthayi hai, mujhe pakka pata hai"), "mixed", "b3_broad",
                    L("You rely on a feeling of certainty rather than a plan.", "Aap plan ki jagah pakke vishwas ke ehsaas par bharosa karte ho."), misconception_signals=["M010"])],
              reasoning_prompt=L("What does this result tell you about how you chose?", "Ye nateeja aapke chunav ke baare mein kya batata hai?"), simulation_hint="concentration")


SC = scenario(
    id="one_basket",
    title=L("Don't Put Everything in One Basket", "Sab Ande Ek Tokri Mein Mat Rakho"),
    tagline=L("A colleague raves about one company. How do you spread — or not?", "Colleague ek company ki tareef karta hai. Aap paisa kaise baantoge — ya nahi?"),
    character={"name": "Imran", "age": 29, "role": "software tester with simulated ₹50,000 to practise with"},
    difficulty=2,
    concept_tags=["diversification", "concentration_risk", "risk"],
    pressure_tags=["social_proof", "greed", "fear"],
    tests=["M004", "M005", "M010", "M009"],
    initial="b1_choose",
    dimensions=["risk_recognition", "concept_knowledge", "independent_reasoning"],
    states=[
        ST("b1_choose", L("A colleague's favourite", "Colleague ki pasandeeda company"),
           L("Imran has a simulated ₹50,000 to practise with. A colleague says Kaveri Solar Ltd (fictional) “can't fail”. Four fictional options are available: Kaveri Solar, Gomti Foods, Narmada Steel and Sutlej Bank, plus Brahmaputra Solar (another solar company). Nothing here is a recommendation about any real asset.",
             "Imran ke paas practice ke liye simulated ₹50,000 hain. Ek colleague kehta hai Kaveri Solar Ltd (kaalpanik) “fail ho hi nahi sakti”. Chaar kaalpanik options hain: Kaveri Solar, Gomti Foods, Narmada Steel aur Sutlej Bank, aur Brahmaputra Solar (ek aur solar company). Yahan kisi asli asset ke baare mein koi sifarish nahi."),
           channel=CH("chat", "Colleague Vikas (fictional)", [L("Kaveri Solar is up 60% this year. It can't fail! Put it all in.", "Kaveri Solar is saal 60% badhi hai. Ye fail nahi ho sakti! Sab isi mein daalo.")]),
           pressure=[P("social_proof", L("“Everyone in the office is in.”", "“Office mein sab ismein hain.”")), P("greed", L("“Up 60% this year.”", "“Is saal 60% badhi.”"))],
           evidence=[
               E("b1_cant", L("“It can't fail”", "“Ye fail nahi ho sakti”"), L("Total certainty from a colleague.", "Colleague ka poora vishwas."), "red_flag",
                 L("No company or sector is immune to bad events. Certainty is a signal to examine, not to relax.", "Koi company ya sector buri ghatnaon se mukt nahi. Pakka vishwas jaanchne ka sanket hai, nishchint hone ka nahi."), "overconfidence"),
               E("b1_past", L("“Up 60% this year”", "“Is saal 60% badhi”"), L("A past gain used as the reason.", "Pichhla faayda wajah ke taur par."), "red_flag",
                 L("Past gains do not tell you about the future and can make a risk look safer than it is.", "Pichhle faayde bhavishya ke baare mein nahi batate aur risk ko surakshit dikha sakte hain."), "past_performance"),
               E("b1_one", L("Everything would depend on one company", "Sab kuch ek company par nirbhar hoga"), L("₹50,000 in a single place.", "₹50,000 ek hi jagah."), "red_flag",
                 L("This is concentration risk: one bad event can hit all of your money at once.", "Ye concentration risk hai: ek buri ghatna aapke poore paise par ek saath asar daal sakti hai."), "concentration"),
               E("b1_sector", L("Solar depends partly on government policy", "Solar kuch had tak sarkari policy par nirbhar hai"), L("Policy changes can move a whole sector.", "Policy badalne se poora sector hil sakta hai."), "neutral",
                 L("Companies in the same sector can fall together — owning two similar companies is not the same as spreading across different areas.", "Ek hi sector ki companies ek saath gir sakti hain — do milti-julti companies rakhna alag-alag kshetron mein baantna nahi."))],
           actions=[
               A("all_in", L("All ₹50,000 in Kaveri Solar — Vikas is confident", "Poora ₹50,000 Kaveri Solar mein — Vikas ko vishwas hai"), "unsafe", "b2_all",
                 L("You put everything into one company.", "Aap sab kuch ek company mein daalte ho."), misconception_signals=["M005"], simple=L("All in one", "Sab ek mein")),
               A("two_solar", L("Split between Kaveri Solar and Brahmaputra Solar — that's diversified", "Kaveri Solar aur Brahmaputra Solar mein baant do — ye diversified hai"), "mixed", "b2_sim",
                 L("You hold two companies from the same sector.", "Aap ek hi sector ki do companies rakhte ho."), misconception_signals=["M004"], simple=L("Two solar companies", "Do solar companies")),
               A("split_four", L("Split equally across four different fictional assets", "Chaar alag kaalpanik assets mein barabar baant do"), "safe", "b2_split",
                 L("You spread the money across four unrelated areas.", "Aap paisa chaar alag kshetron mein baantte ho."), simple=L("Split across four", "Chaar mein baanto")),
               A("buffer_split", L("Keep ₹10,000 aside as an emergency cushion and split the rest across the four", "₹10,000 emergency cushion ke liye rakho aur baaki chaar mein baanto"), "safe", "b2_buf",
                 L("You keep a cushion and spread the rest.", "Aap cushion rakhte ho aur baaki baantte ho."), simple=L("Keep a cushion, split the rest", "Cushion rakho, baaki baanto"))],
           reasoning_prompt=L("Why did you choose this split?", "Aapne ye baantne ka tareeka kyun chuna?"), simulation_hint="concentration"),
        after_event("all", "Everything was in one company.", "Sab kuch ek hi company mein tha."),
        after_event("sim", "Both holdings were solar companies.", "Dono holdings solar companies thi."),
        after_event("split", "The money was spread across four areas.", "Paisa chaar kshetron mein baanta tha."),
        after_event("buf", "A cushion was kept in cash and the rest spread across four areas.", "Cushion cash mein tha aur baaki chaar kshetron mein."),
        ST("b3_broad", L("A different kind of fall", "Ek alag tarah ki giravat"),
           L("A few weeks later a broad downturn hits the whole fictional market: all four companies fall about 12% together, whatever sector they are in. Cash (if any) stays flat.",
             "Kuch hafte baad poore kaalpanik market mein vyapak giravat aati hai: chaaron companies sector chahe jo ho, ek saath lagbhag 12% girti hain. Cash (agar hai) wahi rehta hai."),
           channel=CH("news", "Fictional business news", [L("BROAD SELL-OFF: all sectors lower.", "VYAPAK BIKWALI: sab sector neeche.")]),
           pressure=[P("fear", L("“Diversification doesn't work.”", "“Diversification kaam nahi karta.”"))],
           evidence=[
               E("b3_all", L("Different assets fell together", "Alag assets ek saath gire"), L("This time sector did not matter.", "Is baar sector ne fark nahi daala."), "neutral",
                 L("Diversification reduces concentration risk, but market-wide risk remains. It is a seatbelt, not an invincibility suit.", "Diversification concentration risk ghatata hai, par poore market ka risk rehta hai. Ye seatbelt hai, avijay kavach nahi.")),
               E("b3_claim", L("“Diversification doesn't work”", "“Diversification kaam nahi karta”"), L("An overreaction to one event.", "Ek ghatna par ati-pratikriya."), "red_flag",
                 L("One event where assets fell together does not cancel the earlier lesson; both lessons are true.", "Ek ghatna jisme assets saath gire pichhli seekh ko radd nahi karti; dono baatein sach hain."), "overreaction")],
           actions=[
               A("understand", L("Both are true: spreading helps with one-company risk; it can't remove market-wide risk, so my plan, time horizon and cushion still matter", "Dono sach: baantna ek-company risk mein madad karta hai; poore market ka risk nahi hatata, isliye plan, samay-seema aur cushion zaroori"), "safe", "t_aware",
                 L("You hold two ideas at once, which is what a resilient plan needs.", "Aap do vichar ek saath rakhte ho, jo majboot plan ko chahiye."), verification=True),
               A("fail_conclusion", L("So spreading is pointless — go back to one company", "To baantna bekaar hai — wapas ek company par jao"), "mixed", "t_overreacted",
                 L("You discard a useful tool because it was not magic.", "Aap ek kaam ka aujaar chhod dete ho kyunki wo jaadu nahi tha."), misconception_signals=["M004"]),
               A("eliminated", L("I diversified, so I should not have lost anything", "Maine diversify kiya, to mujhe kuch nahi khona chahiye tha"), "unsafe", "t_overconfident",
                 L("You expected diversification to remove all risk.", "Aapne socha diversification sab risk hata dega."), misconception_signals=["M004"])],
           reasoning_prompt=L("What does diversification do, and what can it not do?", "Diversification kya karta hai, aur kya nahi kar sakta?"), simulation_hint="diversification"),
        END("t_aware", "safe", L("You see both sides", "Aap dono pehlu dekhte ho"), L("Spreading reduces the damage from one thing going wrong, but cannot remove risk that hits everything. Knowing what a tool does — and does not do — is the point.", "Baantna kisi ek cheez ke bigadne ka nuksaan ghatata hai, par sab par asar karne wala risk nahi hata sakta. Aujaar kya karta hai — aur kya nahi — ye jaanna hi mudda hai.")),
        END("t_overreacted", "mixed", L("A tool, not magic", "Aujaar, jaadu nahi"), L("Diversification did its job in the first shock. One broad fall does not make it useless; it makes it incomplete on its own.", "Diversification ne pehle jhatke mein apna kaam kiya. Ek vyapak giravat use bekaar nahi banati; use akele adhoora banati hai.")),
        END("t_overconfident", "unsafe", L("Expecting no risk", "Koi risk nahi, aisi ummeed"), L("Diversification is not risk removal. Believing it is can lead people to take on more risk than they can handle.", "Diversification risk hatana nahi hai. Aisa maanne se log jhelne se zyada risk le sakte hain.")),
        END("t_doubled_down", "unsafe", L("Concentration, again", "Phir wahi concentration"), L("Putting more into the same place right after seeing the effect of concentration is the loss-recovery trap. A bigger bet is not a faster way back.", "Concentration ka asar dekhne ke turant baad usi jagah aur daalna loss-recovery ka jaal hai. Bada daanv wapas aane ka tez raasta nahi.")),
    ],
    reflection={
        "key_points": [
            L("One company or sector can fall a lot at once. Concentration risk is the share of your money exposed to a single event.", "Ek company ya sector ek saath bahut gir sakta hai. Concentration risk wo hissa hai jo ek ghatna se prabhavit hota hai."),
            L("Two similar assets (same sector) are not true diversification.", "Do milti-julti assets (ek hi sector) asli diversification nahi."),
            L("Diversification reduces — it does not eliminate — risk.", "Diversification risk ghatata hai, khatam nahi karta."),
            L("A cushion of easily accessible money is part of a resilient plan.", "Aasani se milne wale paise ka cushion majboot plan ka hissa hai.")],
        "questions": [L("What share of your money depends on one thing?", "Aapke paise ka kitna hissa ek cheez par tika hai?")],
        "micro_lesson": {"concept_id": "concentration_risk", "title": L("The 'what if this one thing fails?' question", "'Agar ye ek cheez fail ho gayi to?' sawaal"),
                         "body": L("For any plan ask: if the biggest piece fell 40%, how much of my total would I lose? If the answer is more than you could handle, the plan is too concentrated.",
                                   "Kisi bhi plan par poochho: agar sabse bada hissa 40% gir jaye to mera kitna kul nuksaan hoga? Agar jawab jhel pane se zyada hai to plan bahut concentrated hai.")},
    },
)
