"use client";
import Link from "next/link";
import { useState } from "react";
import { FingerprintCard } from "./Fingerprint";
import { SpeakButton } from "./SpeakButton";
import { Icon } from "./ui";
import { useApp } from "@/lib/state";
import type { Rec, Summary } from "@/lib/types";

export const Q_STYLE = { safe: "border-emerald/50 bg-emerald-100 text-emerald", mixed: "border-saffron/50 bg-saffron-100 text-[#7a4b06]", unsafe: "border-danger/50 bg-danger-100 text-danger" } as const;

export function RecCard({ rec, selectionId, onStart }: { rec: Rec; selectionId?: number; onStart?: () => void }) {
  const { t } = useApp();
  const [open, setOpen] = useState(false);
  const href = rec.kind === "scenario" ? `/simulate/play?scenario=${rec.id}${selectionId ? `&sel=${selectionId}` : ""}` : rec.kind === "simulation" ? `/learn?tab=sims&sim=${rec.id}` : "/learn?tab=quiz";
  return (
    <div className="card border-saffron/50 bg-saffron-100/50 p-5">
      <p className="eyebrow">{t("next_up")}</p>
      <h3 className="mt-1 text-xl font-bold text-midnight">{rec.title}</h3>
      <p className="mt-2 text-[0.95rem]">{rec.rationale}</p>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Link href={href} onClick={onStart} className="btn-primary">{t("start_next")} <Icon name="arrow" /></Link>
        {rec.reasons.length > 0 && <button className="text-sm font-semibold text-midnight underline" onClick={() => setOpen(!open)} aria-expanded={open}>{t("why_this")}</button>}
      </div>
      {open && (
        <ul className="mt-3 space-y-1 rounded-xl bg-white/70 p-3 text-xs text-ink-muted" aria-label="Selection reasoning">
          {rec.reasons.map((r, i) => <li key={i}>{r}</li>)}
        </ul>
      )}
    </div>
  );
}

export function SummaryView({ s }: { s: Summary }) {
  const { t } = useApp();
  const o = s.outcome;
  const tone = o.kind === "safe" ? "from-emerald to-[#1f5d43]" : o.kind === "mixed" ? "from-saffron to-[#8c590b]" : "from-maroon to-[#511824]";
  return (
    <div className="space-y-6 anim animate-rise" data-testid="summary">
      <section className={`jali overflow-hidden rounded-3xl bg-gradient-to-br ${tone} p-7 text-white`} aria-labelledby="out-h">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-white/80">{t("outcome")} · {s.title}</p>
        <h2 id="out-h" className="mt-1 text-3xl font-bold">{o.headline}</h2>
        <p className="mt-3 max-w-3xl text-lg text-white/95">{o.summary}</p>
        {o.simulated_loss ? <p className="mt-3 inline-block rounded-lg bg-black/25 px-3 py-1.5 text-sm font-semibold">{t("loss_label")}: ₹{o.simulated_loss.toLocaleString("en-IN")} · {t("badge_short")}</p> : null}
        <div className="mt-4"><SpeakButton text={`${o.headline}. ${o.summary}`} className="!border-white/40 !text-white hover:!bg-white/10" /></div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="card p-5" aria-labelledby="dec-h">
          <h3 id="dec-h" className="text-xl font-bold text-midnight">{t("decisions_made")}</h3>
          <ol className="mt-3 space-y-3">
            {s.decisions.map((d, i) => (
              <li key={i} className="rounded-xl border border-line bg-white p-3">
                <p className="text-xs text-ink-faint">{i + 1}. {d.state}</p>
                <p className="mt-0.5 font-semibold">{d.action}</p>
                <p className="mt-1 flex flex-wrap items-center gap-2 text-xs">
                  <span className={`chip ${Q_STYLE[d.quality]}`}>{t(`q_${d.quality}` as any)}</span>
                  {d.latency_s != null && <span className="text-ink-muted"><Icon name="clock" className="mr-1 inline h-3.5 w-3.5" />{d.latency_s}s</span>}
                  {d.confidence != null && <span className="text-ink-muted">{t("confidence")} {d.confidence}/5</span>}
                </p>
              </li>
            ))}
          </ol>
          {s.decision_speed.avg_s != null && <p className="mt-3 text-sm text-ink-muted">{t("avg_speed")}: <b>{s.decision_speed.avg_s}s</b></p>}
          {s.pressure.decisions_under_pressure > 0 && (
            <p className="mt-2 text-sm text-ink-muted">{t("pressure")}: {s.pressure.types.join(", ")} — {s.pressure.held_steady}/{s.pressure.decisions_under_pressure} {t("pressure_held").toLowerCase()}</p>
          )}
        </section>

        <section className="card p-5" aria-labelledby="ev-h">
          <h3 id="ev-h" className="text-xl font-bold text-midnight">{t("evidence")}</h3>
          <h4 className="mt-3 text-sm font-bold uppercase tracking-wide text-emerald">{t("recognized")} ({s.evidence.recognized.length})</h4>
          <ul className="mt-1 space-y-1 text-sm">{s.evidence.recognized.length ? s.evidence.recognized.map((e, i) => <li key={i} className="flex gap-2"><Icon name="check" className="mt-1 h-4 w-4 shrink-0 text-emerald" />{e.label}</li>) : <li className="text-ink-faint">—</li>}</ul>
          <h4 className="mt-4 text-sm font-bold uppercase tracking-wide text-[#7a4b06]">{t("missed")} ({s.evidence.missed.length})</h4>
          <ul className="mt-1 space-y-2 text-sm">{s.evidence.missed.length ? s.evidence.missed.map((e, i) => <li key={i}><span className="font-semibold">{e.label}</span>{e.why && <span className="block text-ink-muted">{e.why}</span>}</li>) : <li className="text-ink-faint">—</li>}</ul>
        </section>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="card p-5" aria-labelledby="beh-h">
          <h3 id="beh-h" className="text-xl font-bold text-midnight">{t("patterns")}</h3>
          <ul className="mt-3 space-y-3">
            {s.behaviours.length ? s.behaviours.slice(0, 5).map((b) => (
              <li key={b.label} className="rounded-xl border border-line bg-white p-3">
                <p className={`text-xs font-bold tracking-wide ${b.positive ? "text-emerald" : "text-maroon"}`}>{b.name}{b.count > 1 ? ` ×${b.count}` : ""}</p>
                <p className="mt-1 text-sm text-ink-muted">{b.explanation}</p>
              </li>
            )) : <li className="text-ink-faint">—</li>}
          </ul>
        </section>
        <section className="card p-5" aria-labelledby="mis-h">
          <h3 id="mis-h" className="text-xl font-bold text-midnight">{t("misconceptions")}</h3>
          <ul className="mt-3 space-y-3">
            {s.misconceptions.length ? s.misconceptions.map((m) => (
              <li key={m.id} className="rounded-xl border border-maroon/30 bg-maroon-100/50 p-3">
                <p className="text-xs font-bold text-maroon">{m.id} · {m.name}</p>
                <p className="mt-1 text-sm">{m.correction}</p>
              </li>
            )) : <li className="text-ink-muted">{t("none_found")}</li>}
            {s.misconceptions_resolved.map((m) => <li key={m.id} className="rounded-xl border border-emerald/40 bg-emerald-100 p-3 text-sm text-emerald"><Icon name="check" className="mr-1 inline h-4 w-4" />{m.name} — resolved</li>)}
          </ul>
        </section>
      </div>

      <section className="card p-5" aria-labelledby="refl-h">
        <h3 id="refl-h" className="text-xl font-bold text-midnight">{t("key_points")}</h3>
        <ul className="mt-3 list-disc space-y-1.5 pl-5">{s.reflection.key_points.map((k, i) => <li key={i}>{k}</li>)}</ul>
        {s.reflection.questions.length > 0 && <p className="mt-4 rounded-xl bg-ivory-100 p-3 text-sm italic text-ink-muted">{s.reflection.questions.join("  ·  ")}</p>}
      </section>

      <section className="card border-saffron/40 bg-saffron-100/40 p-5" aria-labelledby="lesson-h">
        <p className="eyebrow">{t("micro_lesson")}</p>
        <h3 id="lesson-h" className="mt-1 text-xl font-bold text-midnight">{s.micro_lesson.title}</h3>
        <p className="mt-2">{s.micro_lesson.body}</p>
        <div className="mt-3 flex flex-wrap gap-3"><SpeakButton text={`${s.micro_lesson.title}. ${s.micro_lesson.body}`} /><Link href={`/learn?tab=concepts&concept=${s.micro_lesson.concept_id}`} className="btn-ghost !min-h-[40px] !py-1.5 text-sm">{t("tab_concepts")}</Link></div>
      </section>

      <FingerprintCard fp={s.fingerprint} />

      {s.next.scenario && <RecCard rec={s.next.scenario} selectionId={s.next.selection_id} />}
      {s.next.other_training.length > 0 && (
        <ul className="grid gap-3 sm:grid-cols-2">
          {s.next.other_training.slice(0, 2).map((r) => (
            <li key={r.id} className="card p-4 text-sm"><p className="font-bold text-midnight">{r.title}</p><p className="mt-1 text-ink-muted">{r.rationale}</p>
              <Link href={r.kind === "simulation" ? `/learn?tab=sims&sim=${r.id}` : "/learn?tab=quiz"} className="mt-2 inline-block font-semibold underline">{t("see_sim")}</Link></li>
          ))}
        </ul>
      )}
      <div className="flex flex-wrap gap-3 pb-6"><Link href="/resilience" className="btn-night">{t("view_report")} <Icon name="arrow" /></Link><Link href="/simulate" className="btn-ghost">{t("nav_simulate")}</Link></div>
    </div>
  );
}
