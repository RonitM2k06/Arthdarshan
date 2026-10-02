"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { LineChart } from "@/components/Charts";
import { Radar, type FP } from "@/components/Fingerprint";
import { RecCard, Q_STYLE } from "@/components/Summary";
import { Empty, ErrorBox, Icon, PageHead, Spinner } from "@/components/ui";
import { api } from "@/lib/api";
import { useApp } from "@/lib/state";
import type { Next } from "@/lib/types";

type Dash = {
  fingerprint: FP; scenarios_completed: number; scenarios_total: number; concepts_mastered: number; concepts_total: number; misconceptions_resolved: number; misconceptions_active: number;
  streak_days: number; recent_decisions: { scenario: string; situation: string; action: string; quality: "safe" | "mixed" | "unsafe"; latency_s: number | null }[];
  improvement: { points: { overall: number }[] }; recommendation: Next;
};

function Tile({ label, value, of, note }: { label: string; value: number; of?: number; note?: string }) {
  const frac = of ? Math.min(1, value / of) : null, r = 26, c = 2 * Math.PI * r;
  return (
    <div className="card flex items-center gap-4 p-4">
      {frac != null ? (
        <svg width="64" height="64" viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r={r} fill="none" stroke="#EDE3C9" strokeWidth="7" /><circle cx="32" cy="32" r={r} fill="none" stroke="#3A5FA0" strokeWidth="7" strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c * (1 - frac)} transform="rotate(-90 32 32)" /></svg>
      ) : <span className="grid h-16 w-16 place-items-center rounded-full bg-saffron-100 text-2xl" aria-hidden="true">✦</span>}
      <div><p className="font-serif text-3xl font-bold leading-none text-midnight">{value}{of ? <span className="text-lg text-ink-faint">/{of}</span> : null}</p><p className="mt-1 text-sm font-semibold text-ink-muted">{label}</p>{note && <p className="text-xs text-ink-faint">{note}</p>}</div>
    </div>
  );
}

export default function Progress() {
  const { t, lang, user } = useApp();
  const [d, setD] = useState<Dash | null>(null);
  const [err, setErr] = useState(false);
  const load = useCallback(() => { setErr(false); api<Dash>("/progress").then(setD).catch(() => setErr(true)); }, []);
  useEffect(() => { if (user) load(); }, [user, lang, load]);
  if (err) return <ErrorBox onRetry={load} />;
  if (!d) return <Spinner />;
  return (
    <div className="space-y-8">
      <PageHead eyebrow={t("nav_progress")} title={t("dash_title")} sub={t("badge_short")} />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" data-testid="tiles">
        <Tile label={t("scenarios_done")} value={d.scenarios_completed} of={d.scenarios_total} />
        <Tile label={t("concepts_mastered")} value={d.concepts_mastered} of={d.concepts_total} />
        <Tile label={t("misc_resolved")} value={d.misconceptions_resolved} note={`${d.misconceptions_active} active`} of={Math.max(d.misconceptions_resolved + d.misconceptions_active, 1)} />
        <Tile label={t("streak")} value={d.streak_days} />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="card p-5" aria-labelledby="fp2-h"><h2 id="fp2-h" className="text-xl font-bold text-midnight">{t("fp_title")}</h2><p className="mt-1 text-sm text-ink-muted">{d.fingerprint.summary}</p><Radar dims={d.fingerprint.dimensions} size={380} />
          <Link href="/resilience" className="btn-ghost mt-2">{t("view_report")} <Icon name="arrow" /></Link></section>
        <div className="space-y-6">
          <section className="card p-5" aria-labelledby="tr-h"><h2 id="tr-h" className="text-xl font-bold text-midnight">{t("trend")}</h2>
            {d.improvement.points.length >= 2 ? <LineChart series={[{ name: t("score"), points: d.improvement.points.map((p) => p.overall) }]} xLabel="#" yLabel={t("trend")} money={false} height={210} /> : <p className="mt-2 text-ink-muted">{t("empty_resilience")}</p>}</section>
          <section className="card p-5" aria-labelledby="rd-h"><h2 id="rd-h" className="text-xl font-bold text-midnight">{t("recent")}</h2>
            {d.recent_decisions.length ? <ul className="mt-3 space-y-2" data-testid="recent">{d.recent_decisions.map((x, i) => <li key={i} className="rounded-lg border border-line bg-white p-2.5 text-sm"><p className="text-xs text-ink-faint">{x.scenario} · {x.situation}</p><p className="font-semibold">{x.action}</p><span className={`chip mt-1 ${Q_STYLE[x.quality]}`}>{t(`q_${x.quality}` as any)}</span>{x.latency_s != null && <span className="ml-2 text-xs text-ink-muted">{x.latency_s}s</span>}</li>)}</ul> : <Empty>{t("empty_resilience")}</Empty>}</section>
        </div>
      </div>
      {d.recommendation.scenario && <RecCard rec={d.recommendation.scenario} />}
    </div>
  );
}
