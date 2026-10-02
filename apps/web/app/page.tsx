"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Mark } from "@/components/Logo";
import { Radar, type Dim } from "@/components/Fingerprint";
import { Icon, SimBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { useApp } from "@/lib/state";

// Illustrative preview only (labelled as such). A learner's real fingerprint is computed from their own decisions.
const SAMPLE: Dim[] = [
  ["concept_knowledge", "Concepts", 76, 70], ["risk_recognition", "Risk", 84, 78], ["evidence_verification", "Verification", 61, 40], ["scam_awareness", "Scams", 72, 55],
  ["fomo_resistance", "FOMO", 42, 30], ["herd_resistance", "Herd", 58, 50], ["emotional_discipline", "Emotions", 66, 60], ["independent_reasoning", "Reasoning", 69, 52],
  ["uncertainty_awareness", "Uncertainty", 63, 58], ["terminology", "Terminology", 71, 62],
].map(([id, short, score, prev]) => ({ id: id as string, name: short as string, short: short as string, score: score as number, previous: prev as number, change: (score as number) - (prev as number), n_observations: 0, evidence: [], measured: true }));

export default function Landing() {
  const { t, lang } = useApp();
  const [cards, setCards] = useState<{ id: string; title: string; tagline: string; difficulty: number }[]>([]);
  useEffect(() => { api<{ scenarios: any[] }>("/scenarios").then((r) => setCards(r.scenarios)).catch(() => setCards([])); }, [lang]);
  const steps = ["how_1", "how_2", "how_3", "how_4", "how_5", "how_6"] as const;
  return (
    <div className="-mx-4 -mt-8">
      {/* HERO */}
      <section className="jali relative overflow-hidden bg-midnight px-4 pb-16 pt-14 text-ivory sm:pt-20">
        <div aria-hidden="true" className="pointer-events-none absolute -right-24 -top-24 h-96 w-96 rounded-full border border-saffron-300/20" />
        <div aria-hidden="true" className="pointer-events-none absolute -right-10 top-10 h-64 w-64 rounded-full border border-saffron-300/20" />
        <div className="mx-auto grid max-w-6xl items-center gap-10 lg:grid-cols-[1.1fr_.9fr]">
          <div className="anim animate-rise">
            <div className="mb-5 flex items-center gap-3"><Mark size={44} /><SimBadge dark short /></div>
            <h1 className="break-words font-serif text-4xl font-bold tracking-[0.04em] min-[400px]:text-5xl sm:text-6xl sm:tracking-[0.06em]">ARTHDARSHAN</h1>
            <p className="mt-3 font-serif text-2xl italic text-saffron-300 sm:text-3xl">{t("tagline")}</p>
            <p className="mt-5 max-w-xl text-lg text-ivory/90">{t("hero_sub")}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/simulate" className="btn-primary !px-7 !py-3.5 text-base">{t("cta_enter")} <Icon name="arrow" /></Link>
              <Link href="/learn?tab=ask" className="btn border-saffron-300/60 text-saffron-300 hover:bg-midnight-700"><Icon name="mic" /> {t("cta_voice")}</Link>
              <Link href="/resilience" className="btn border-ivory/30 text-ivory hover:bg-midnight-700">{t("cta_view")}</Link>
            </div>
          </div>
          {/* a taste of the experience in the first second */}
          <div className="anim animate-rise rounded-3xl border border-saffron-300/30 bg-midnight-800/80 p-5 shadow-2xl" aria-label="Preview of the simulator">
            <div className="mb-3 flex items-center justify-between text-xs text-ivory/70"><span>Rahul, 24 · first-time investor</span><SimBadge dark short /></div>
            <div className="rounded-2xl bg-ivory p-4 text-ink">
              <p className="text-xs font-bold text-midnight-600">Aarav Mehta · WealthWave Circle <span className="font-normal text-ink-faint">(fictional)</span></p>
              <p className="mt-2 space-y-1 text-[0.95rem] leading-snug"><span className="block">“SEBI registered opportunity.</span><span className="block"><b>Guaranteed 30% returns.</b></span><span className="block">Only 10 slots remaining.</span><span className="block">Invest today.”</span></p>
            </div>
            <div className="mt-3 flex items-center gap-3 rounded-xl border border-saffron-300/30 px-3 py-2 text-sm text-saffron-300">
              <Icon name="clock" /> <span className="font-semibold">0:45</span> <span className="text-ivory/75">· urgency · scarcity · authority</span>
            </div>
            <div className="mt-3 grid gap-2 text-sm font-semibold text-midnight sm:grid-cols-2" aria-hidden="true">
              {["Invest now", "Ask for proof", "Look into it myself", "Walk away"].map((a) => <span key={a} className="rounded-xl bg-ivory/95 px-3 py-2.5">{a}</span>)}
            </div>
            <p className="mt-3 text-xs text-ivory/65">No “correct answer” banner. You decide — then see what happens, and how you decided.</p>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl px-4">
        {/* WHAT / LOOP */}
        <section className="py-14" aria-labelledby="what-h">
          <p className="eyebrow">01</p>
          <h2 id="what-h" className="mt-1 text-3xl font-bold text-midnight">{t("what_title")}</h2>
          <p className="mt-3 max-w-3xl text-lg text-ink-muted">{t("what_body")}</p>
          <ol className="mt-8 grid gap-3 sm:grid-cols-3 lg:grid-cols-6" aria-label={t("how_title")}>
            {steps.map((k, i) => (
              <li key={k} className="card relative p-4 text-center">
                <span className="mx-auto mb-2 grid h-9 w-9 place-items-center rounded-full bg-midnight font-serif text-lg font-bold text-saffron-300">{i + 1}</span>
                <span className="text-sm font-semibold text-midnight">{t(k)}</span>
              </li>
            ))}
          </ol>
        </section>

        {/* WHY */}
        <section className="jali-light rounded-3xl border border-line bg-ivory-100 p-8 sm:p-12" aria-labelledby="why-h">
          <p className="eyebrow">02</p>
          <h2 id="why-h" className="mt-1 text-3xl font-bold text-midnight">{t("why_title")}</h2>
          <p className="mt-3 max-w-3xl text-lg text-ink-muted">{t("why_body")}</p>
        </section>

        {/* SCENARIOS */}
        <section className="py-14" aria-labelledby="sc-h">
          <p className="eyebrow">03</p>
          <h2 id="sc-h" className="mt-1 text-3xl font-bold text-midnight">{t("scenarios_title")}</h2>
          <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {cards.map((c) => (
              <li key={c.id}>
                <Link href={`/simulate/play?scenario=${c.id}`} className="card block h-full p-5 transition-shadow hover:shadow-lg">
                  <span className="chip border-line bg-ivory-100 text-ink-muted">{t("difficulty")} {"●".repeat(c.difficulty)}{"○".repeat(3 - c.difficulty)}</span>
                  <h3 className="mt-3 text-lg font-bold leading-tight text-midnight">{c.title}</h3>
                  <p className="mt-1.5 text-sm text-ink-muted">{c.tagline}</p>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        {/* FINGERPRINT PREVIEW */}
        <section className="rounded-3xl bg-midnight p-6 text-ivory sm:p-12" aria-labelledby="fp-prev-h">
          <div className="grid items-center gap-8 lg:grid-cols-2">
            <div>
              <p className="eyebrow !text-saffron-300">04</p>
              <h2 id="fp-prev-h" className="mt-1 text-3xl font-bold">{t("fp_title")}</h2>
              <p className="mt-3 text-ivory/85">10 dimensions · FOMO · herd behaviour · verification · uncertainty · terminology…</p>
              <p className="mt-3 text-sm text-saffron-300">{t("fp_preview_note")}</p>
            </div>
            <div className="rounded-2xl bg-ivory p-3"><Radar dims={SAMPLE} /></div>
          </div>
        </section>

        {/* SAFETY */}
        <section className="py-14" aria-labelledby="safe-h">
          <div className="grid gap-8 lg:grid-cols-2">
            <div>
              <p className="eyebrow">05</p>
              <h2 id="safe-h" className="mt-1 text-3xl font-bold text-midnight">{t("safety_title")}</h2>
              <p className="mt-3 text-lg text-ink-muted">{t("safety_body")}</p>
            </div>
            <div className="card p-6">
              <h3 className="mb-3 font-serif text-xl font-bold text-maroon">{t("never_title")}</h3>
              <ul className="space-y-2.5">
                {(["never_1", "never_2", "never_3", "never_4"] as const).map((k) => (
                  <li key={k} className="flex items-start gap-3"><span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-maroon-100 text-maroon"><Icon name="x" className="h-3.5 w-3.5" /></span>{t(k)}</li>
                ))}
              </ul>
              <Link href="/learn?tab=safety" className="btn-ghost mt-5"><Icon name="shield" /> {t("tab_safety")}</Link>
            </div>
          </div>
        </section>

        <p className="mx-auto max-w-2xl pb-6 text-center font-serif text-2xl italic text-midnight">{t("ending")}</p>
      </div>
    </div>
  );
}
