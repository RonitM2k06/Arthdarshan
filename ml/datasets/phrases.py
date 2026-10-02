"""Phrase banks for SYNTHETIC training data. Everything generated from these is labelled synthetic.

Misconception claims are written by the project team as plausible learner statements in English and Hinglish.
A separate, differently-worded, hand-written held-out set (heldout_misconception.json) is NOT generated from these banks.
"""

MISC_CLAIMS: dict[str, list[str]] = {
    "M001": ["it is guaranteed so there is no risk", "guaranteed returns means I cannot lose", "they promised fixed 30% returns so it is safe", "the return is assured",
             "pakka return milega isliye safe hai", "guarantee diya hai to risk nahi hai", "risk free high returns sounds perfect", "they said there is no loss at all",
             "returns are fixed and certain", "sure profit is promised", "100% safe guaranteed income", "yeh scheme pakka munafa deti hai"],
    "M002": ["so many people joined so it must be genuine", "everyone in the group is investing so it is fine", "thousands of members cannot be wrong", "the group is huge so it is legit",
             "sab log kar rahe hain to sahi hi hoga", "itne saare members hain to asli hai", "everybody is making money so I trust it", "if so many people trust it then it is safe",
             "the crowd is investing so it works", "240 members are in so it has to be real", "bahut log jud gaye hain isliye safe hai"],
    "M003": ["it gave 85% last quarter so it will do that again", "past returns were great so I expect the same next year", "their track record shows I will earn the same",
             "pichhle saal itna return diya to is saal bhi dega", "the last 3 months were amazing so it will continue", "it always performed well so it will keep doing so",
             "history proves I will profit again", "isne pichhli baar achha diya to aage bhi dega", "last year's chart tells me this year is the same"],
    "M004": ["I spread my money across many things so I can't lose", "diversified means no risk at all", "if I buy ten different stocks nothing can go wrong",
             "alag alag jagah lagaya hai to risk khatam", "with a diversified portfolio I will never lose money", "many funds so a loss is impossible",
             "two solar companies is diversified so I am fully safe", "spreading it out removes the danger completely", "diversification se koi nuksaan nahi hota"],
    "M005": ["the higher return is clearly the better choice", "30% is better than 8% so I take it", "more returns means a better opportunity", "sabse zyada return wala sabse achha hai",
             "I always pick the highest return", "bigger profit promised so it is the better scheme", "why would I take lower returns when this pays more",
             "zyada munafa matlab behtar plan", "the plan with higher percentage must be superior"],
    "M006": ["only 10 slots left so I must join right now", "the offer ends today so I have to hurry", "it is the last chance so I cannot wait", "abhi nahi liya to mauka chala jayega",
             "slots are filling so I need to act quickly", "if I wait it will be gone", "the timer is running so I should decide immediately", "deadline hai isliye jaldi karna padega",
             "I do not want to miss out so I am joining now", "limited time so I must act fast", "sirf kuch slots bache hain isliye abhi judna padega"],
    "M007": ["it says SEBI registered so it is safe", "they have a government certificate so it is genuine", "official approval means it must be legit", "registered hai isliye sahi hai",
             "the certificate looks real so I trust them", "a regulated company cannot cheat", "sarkari mohar hai to bharosa kar sakte hain", "since they mention SEBI I believe them",
             "they are certified so no need to check"],
    "M008": ["it sounds very technical and professional so they must be experts", "the document is full of difficult words so it is credible", "such complicated terms mean it is a serious product",
             "bade bade english words hain to sahi hi hoga", "I did not understand it but it sounds smart so I trust it", "fancy jargon proves they know finance",
             "itni mushkil language hai to company bharosemand hogi", "professional sounding terms mean a genuine product"],
    "M009": ["it is only a small amount so there is no real risk", "just 500 rupees to try, it cannot hurt", "thoda sa paisa hai to risk nahi", "I will test with a tiny amount, safe enough",
             "a small investment means low risk", "bas chhota amount hai kuch nahi hoga", "a little money cannot be a scam", "starting small makes it safe to try"],
    "M010": ["I already paid so I will pay again to get it back", "I must recover my loss quickly", "one more payment and I will win it all back", "nuksaan wapas paane ke liye aur paisa daalunga",
             "I have come this far so I cannot stop now", "I will average down to recover faster", "I will double the money to cover the loss", "itna de diya hai ab ruk nahi sakta",
             "to get my money back I need to put in more"],
    "M011": ["my friend invested so it must be safe", "my cousin told me so I trust it", "bhai ne bataya hai to sahi hoga", "she is my friend so she would not lie", "dost ne kaha isliye bharosa hai",
             "my colleague made money so it is probably fine", "family recommended it so that is enough for me", "Neha is already in so I do not need to check"],
    "M012": ["the fee is only 2% so it does not matter", "the charges are small so I will ignore them", "fees do not really affect the final amount", "2.5% kuch nahi hota",
             "a small yearly cost makes no difference", "the expense ratio is tiny so who cares", "both plans end up roughly the same", "fees se kuch fark nahi padta"],
    "M013": ["we can do the nominee paperwork later", "nomination is not needed right now", "if something happens we will see then", "documents baad mein dekh lenge",
             "nomination abhi zaroori nahi hai", "no need to organise papers now", "there is no hurry about the will", "paperwork can wait until it is needed"],
}

NONE_STATEMENTS = [
    "nobody can guarantee returns so I will check first", "I will verify the registration on the official website", "friends joining is not proof so I will wait",
    "the deadline is just pressure so I will walk away", "I want all charges in writing before deciding", "I am not sure so I will ask someone I trust",
    "ye scam lag raha hai main verify karunga", "guarantee ka matlab red flag hai", "main official site par check karunga", "I would walk away from this",
    "fees compound so I will compare the net amounts", "diversifying reduces concentration risk but not market risk", "I do not know what to do", "this is confusing to me",
    "let me think about it", "ok", "main sochta hoon", "what happens next", "I will look at the evidence first", "mujhe thoda time chahiye",
    "I need a plain language explanation first", "it may be risky so I will read the documents", "saboot dekhe bina paisa nahi dunga", "that sounds too good to be true",
]

OPENERS = ["", "", "", "I think ", "Honestly, ", "To me, ", "Well, ", "I feel ", "mujhe lagta hai ", "Basically ", "Look, ", "My view: "]
CLOSERS = ["", "", "", ".", " so I will go ahead.", " that's why I chose this.", " right?", " isliye yahi sahi hai.", ", simple.", " for me."]
CONTEXTS = ["", "", "", "About this scheme: ", "Regarding the offer: ", "In this scenario, ", "Telegram group: ", "Is scheme ke baare mein: "]

BEHAVIOUR_PHRASES: dict[str, list[str]] = {
    "social_proof_reliance": ["everyone in the group is investing so I will too", "so many members joined so it works", "the whole crowd cannot be wrong", "sab log kar rahe hain to main bhi karunga",
                              "lots of people in the chat made money", "itne log hain group mein isliye theek hai", "it is trending so it must be fine"],
    "friend_reliance": ["my friend invested so I trust it", "my cousin recommended it", "bhai ne bataya isliye sahi hai", "Neha said it is legit", "my colleague told me about it so I believe him",
                        "dost ne kaha hai to bharosa hai", "family member vouched for it"],
    "authority_reliance": ["it says SEBI registered so it is fine", "they have a certificate so it must be legit", "an expert fund manager runs it so I trust it", "government approved hai isliye theek hai",
                           "the official looking document convinces me", "they are certified professionals so safe"],
    "urgency_reaction": ["only a few slots left so I must hurry", "the timer is running so I will join now", "last chance so I cannot wait", "I do not want to miss out", "abhi nahi liya to mauka chhoot jayega",
                         "deadline hai jaldi karna padega", "I need to act immediately"],
    "greed_driven": ["30% returns is amazing I want that", "such high returns can make me rich", "double my money quickly sounds great", "ooncha return milega to main le lunga", "easy money opportunity",
                     "85% profit is a jackpot", "zyada munafa mil raha hai"],
    "fear_panic": ["I am scared of losing everything so I will sell it all", "I panicked when I saw the fall", "darr lag raha hai sab bech dunga", "I am very worried and anxious", "ghabrahat mein sab bech do",
                   "I cannot watch this anymore I will sell everything", "terrified of more losses"],
    "loss_chasing": ["I have already paid so I will pay more to recover it", "I must win back the loss", "come this far so I cannot stop", "nuksaan wapas paane ke liye aur lagaunga", "average down to recover",
                     "double down to cover my loss", "itna de diya ab ruk nahi sakta"],
    "evidence_seeking": ["I will verify it on the official website", "I want to check the registration myself", "let me research and look it up first", "main pehle jaanch karunga", "I need independent proof",
                         "I will search for evidence before paying", "official site par confirm karunga", "I will investigate before deciding"],
    "independent_reasoning": ["because nobody can guarantee 30% I will check the evidence myself", "since there is no proof I will not join", "my own reasoning says the fee before withdrawal is a risk",
                              "isliye kyunki guarantee nahi ho sakti main khud check karunga", "I decided on my own because the evidence is missing", "the risk is clear to me because of the charges"],
    "uncertainty_acknowledgement": ["no one knows what will happen next", "I am not sure about the future", "it depends and nobody can predict", "pata nahi aage kya hoga", "returns are uncertain",
                                    "nobody can predict the market", "koi nahi jaanta aage kya hoga"],
    "deliberate_pause": ["I will pause and think first", "let me wait and sleep on it", "I will take my time", "main thoda ruk kar sochunga", "let me calm down before deciding",
                         "I will slow down and step back", "pehle shaant hokar sochta hoon"],
    "overconfidence": ["I am 100% sure it will go up", "it definitely cannot fail", "I am certain this will work", "pakka badhega mujhe pata hai", "no doubt at all it will succeed",
                       "this is bound to make profit", "I know for sure"],
}
BEHAVIOUR_NONE = ["okay", "I do not know", "this is confusing", "what next", "hmm", "main nahi jaanta", "tell me more", "the message arrived on Telegram", "it has ten slots"]
