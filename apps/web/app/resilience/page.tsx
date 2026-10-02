"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { LineChart } from "@/components/Charts";
import { FingerprintCard, type FP } from "@/components/Fingerprint";
import { RecCard } from "@/components/Summary";
import { Empty, ErrorBox, Icon, PageHead, Spinner } from "@/components/ui";
import { api } from "@/lib/api";
import { useApp } from "@/lib/state";
import type { Next } from "@/lib/types";

type Report = {
  fingerprint: FP; insights: string[]; totals: { decisions: number; scenarios_completed: number };
  recognized: { label: string; why: string | null; times: number; scenario: string }[]; missed: { label: string; why: string | null; times: number; scenario: string }[];
  behaviours: { label: string; name: string; positive: boolean; explanation: string; count: number }[];
  misconceptions: { id: string; name: string; correction: string; detections: number; exposures: number; status: string; clean_streak: number }[];
  concept_mastery: { id: string; name: string; mastery: number; attempts: number; mastered: boolean }[];
  scenario_performance: { session_id: string; title: string; outcome: string; headline: string; completed_at: string; decisions: number; simulated_loss: number | null }[];
  decision_speed: { median_s: number | null; under_time_pressure_median_s: number | null; without_time_pressure_median_s: number | null; unsafe_choices_median_s: number | null; safe_choices_median_s: number | null; n: number };
  evidence_usage: { verification_rate_overall: number | null; verification_rate_under_time_pressure: number | null; verification_rate_without_time_pressure: number | null; avg_warning_sign_recall: number | null };
  recommended_training: Next; improvement: { points: { index: number; scenario: string | null; overall: number; dimensions: Record<string, number> }[]; first_to_latest: Record<string, number> | null };
};

const pct = (v: number | null) => (v == null ? "—" : `${Math.round(v * 100)}%`);
const STATUS = { active: "border-danger/40 bg-danger-100 text-danger", improving: "border-saffron/40 bg-saffron-100 text-[#7a4b06]", resolved: "border-emerald/40 bg-emerald-100 text-emerald" } as const;

export default function Resilience() {
  const { t, lang, user } = useApp();
  const [r, setR] = useState<Report | null>(null);
  const [err, setErr] = useState(false);
  const load = useCallback(() => { setErr(false); api<Report>("/resilience/report").then(setR).catch(() => setErr(true)); }, []);
  useEffect(() => { if (user) load(); }, [user, lang, load]);
  if (err) return <ErrorBox onRetry={load} />;
  if (!r) return <Spinner />;
  const empty = r.totals.decisions === 0;
  const trend = r.improvement.points.length ? [{ name: t("score"), points: r.improvement.points.map((p) => p.overall) }] : [];
  return (
    <div className="space-y-8">
      <PageHead eyebrow={t("badge_short")} title={t("nav_resilience")} sub={t("fp_how")}
        right={<button className="btn-ghost print:hidden" onClick={() => window.print()}>Print / PDF</button>} />
      {empty ? (
        <Empty><p className="mb-4 text-lg">{t("empty_resilience")}</p><Link href="/simulate" className="btn-primary">{t("cta_enter")} <Icon name="arrow" /></Link></Empty>
      ) : (
        <>
          <FingerprintCard fp={r.fingerprint} />
          {r.insights.length > 0 && (
            <section className="card border-saffron/40 bg-saffron-100/50 p-5" aria-labelledby="ins-h">
              <h2 id="ins-h" className="text-xl font-bold text-midnight">{t("rep_insights")}</h2>
              <ul className="mt-2 list-disc space-y-1.5 pl-5" data-testid="insights">{r.insights.map((s, i) => <li key={i}>{s}</li>)}</ul>
            </section>
          )}
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="card p-5" aria-labelledby="rec-h"><h2 id="rec-h" className="text-xl font-bold text-emerald">{t("rep_recognized")}</h2>
              <ul className="mt-3 space-y-2">{r.recognized.length ? r.recognized.map((x, i) => <li key={i} className="flex gap-2 text-sm"><Icon name="check" className="mt-0.5 h-4 w-4 shrink-0 text-emerald" /><span><b>{x.label}</b> <span className="text-ink-faint">×{x.times} · {x.scenario}</span></span></li>) : <li className="text-ink-faint">—</li>}</ul></section>
            <section className="card p-5" aria-labelledby="mis2-h"><h2 id="mis2-h" className="text-xl font-bold text-[#7a4b06]">{t("rep_missed")}</h2>
              <ul className="mt-3 space-y-2">{r.missed.length ? r.missed.map((x, i) => <li key={i} className="text-sm"><b>{x.label}</b> <span className="text-ink-faint">×{x.times} · {x.scenario}</span>{x.why && <span className="block text-ink-muted">{x.why}</span>}</li>) : <li className="text-ink-faint">—</li>}</ul></section>
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="card p-5" aria-labelledby="pat-h"><h2 id="pat-h" className="text-xl font-bold text-midnight">{t("rep_patterns")}</h2>
              <ul className="mt-3 space-y-2.5">{r.behaviours.slice(0, 6).map((b) => <li key={b.label} className="rounded-xl border border-line bg-white p-3"><p className={`text-xs font-bold ${b.positive ? "text-emerald" : "text-maroon"}`}>{b.name} ×{b.count}</p><p className="text-sm text-ink-muted">{b.explanation}</p></li>)}</ul></section>
            <section className="card p-5" aria-labelledby="mis-h"><h2 id="mis-h" className="text-xl font-bold text-midnight">{t("rep_misc")}</h2>
              <ul className="mt-3 space-y-2.5">{r.misconceptions.length ? r.misconceptions.map((m) => (
                <li key={m.id} className="rounded-xl border border-line bg-white p-3"><div className="flex flex-wrap items-center gap-2"><b className="text-sm text-maroon">{m.id} · {m.name}</b><span className={`chip ${STATUS[m.status as keyof typeof STATUS] ?? ""}`}>{m.status}</span></div>
                  <p className="mt-1 text-sm text-ink-muted">{m.correction}</p><p className="mt-1 text-xs text-ink-faint">{m.detections}× detected · {m.exposures}× tested again · clean streak {m.clean_streak}</p></li>)) : <li className="text-ink-muted">{t("none_found")}</li>}</ul></section>
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="card p-5" aria-labelledby="cm-h"><h2 id="cm-h" className="text-xl font-bold text-midnight">{t("rep_mastery")}</h2>
              <ul className="mt-3 space-y-2">{r.concept_mastery.slice(0, 10).map((c) => (
                <li key={c.id}><div className="flex justify-between text-sm"><span>{c.name}</span><span className="font-semibold">{Math.round(c.mastery * 100)}%{c.mastered && " ✓"}</span></div>
                  <div className="mt-1 h-2 overflow-hidden rounded-full bg-ivory-200" aria-hidden="true"><div className="h-full rounded-full bg-series-green" style={{ width: `${c.mastery * 100}%` }} /></div></li>))}</ul></section>
            <section className="card p-5" aria-labelledby="sp-h"><h2 id="sp-h" className="text-xl font-bold text-midnight">{t("rep_perf")}</h2>
              <ul className="mt-3 space-y-2">{r.scenario_performance.map((s) => <li key={s.session_id} className="flex items-center justify-between gap-3 rounded-lg border border-line bg-white px-3 py-2 text-sm"><span><b>{s.title}</b><span className="block text-xs text-ink-faint">{s.headline}</span></span><span className={`chip ${s.outcome === "safe" ? "border-emerald/40 bg-emerald-100 text-emerald" : s.outcome === "mixed" ? "border-saffron/40 bg-saffron-100 text-[#7a4b06]" : "border-danger/40 bg-danger-100 text-danger"}`}>{s.outcome}</span></li>)}</ul></section>
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="card p-5" aria-labelledby="sd-h"><h2 id="sd-h" className="text-xl font-bold text-midnight">{t("rep_speed")}</h2>
              <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
                {[["Median", r.decision_speed.median_s], ["Under time pressure", r.decision_speed.under_time_pressure_median_s], ["Without time pressure", r.decision_speed.without_time_pressure_median_s], ["Unsafe choices", r.decision_speed.unsafe_choices_median_s], ["Safe choices", r.decision_speed.safe_choices_median_s]].map(([k, v]) => <div key={k as string} className="rounded-lg bg-ivory-100 p-2.5"><dt className="text-xs text-ink-muted">{k}</dt><dd className="font-serif text-xl font-bold">{v == null ? "—" : `${v}s`}</dd></div>)}</dl></section>
            <section className="card p-5" aria-labelledby="eu-h"><h2 id="eu-h" className="text-xl font-bold text-midnight">{t("rep_evidence")}</h2>
              <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
                {[["Warning signs noticed", pct(r.evidence_usage.avg_warning_sign_recall)], ["Verified independently", pct(r.evidence_usage.verification_rate_overall)], ["…under time pressure", pct(r.evidence_usage.verification_rate_under_time_pressure)], ["…without time pressure", pct(r.evidence_usage.verification_rate_without_time_pressure)]].map(([k, v]) => <div key={k} className="rounded-lg bg-ivory-100 p-2.5"><dt className="text-xs text-ink-muted">{k}</dt><dd className="font-serif text-xl font-bold">{v}</dd></div>)}</dl></section>
          </div>
          <section className="card p-5" aria-labelledby="imp-h"><h2 id="imp-h" className="text-xl font-bold text-midnight">{t("rep_improve")}</h2>
            {r.improvement.points.length >= 2 ? <div className="mt-3"><LineChart series={trend} xLabel="Scenario #" yLabel="Average fingerprint score" money={false} height={240} />
              {r.improvement.first_to_latest && <ul className="mt-3 flex flex-wrap gap-2 text-xs">{Object.entries(r.improvement.first_to_latest).map(([k, v]) => <li key={k} className={`chip ${v >= 0 ? "border-emerald/40 bg-emerald-100 text-emerald" : "border-danger/40 bg-danger-100 text-danger"}`}>{k.replace(/_/g, " ")} {v >= 0 ? "▲" : "▼"} {Math.abs(v)}</li>)}</ul>}</div>
              : <p className="mt-2 text-ink-muted">Play a second scenario to see change over time.</p>}</section>
          {r.recommended_training.scenario && <RecCard rec={r.recommended_training.scenario} />}
          <p className="text-xs text-ink-faint">{(r as any).generated_from}</p>
        </>
      )}
    </div>
  );
}
