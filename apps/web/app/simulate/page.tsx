"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { RecCard } from "@/components/Summary";
import { ErrorBox, Icon, PageHead, SimBadge, Spinner } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { useApp } from "@/lib/state";
import type { Card, Next } from "@/lib/types";

export default function SimulateHome() {
  const { t, lang, user } = useApp();
  const [data, setData] = useState<{ scenarios: Card[]; recommendation: Next } | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const load = useCallback(() => {
    setErr(null);
    api<{ scenarios: Card[]; recommendation: Next }>("/scenarios").then(setData).catch((e) => setErr(e instanceof ApiError ? e.message : "error"));
  }, []);
  useEffect(() => { if (user) load(); }, [user, lang, load]);
  if (err) return <ErrorBox onRetry={load} />;
  if (!data) return <Spinner />;
  const rec = data.recommendation.scenario;
  return (
    <>
      <PageHead eyebrow={t("nav_simulate")} title={t("sim_title")} sub={t("sim_sub")} right={<SimBadge />} />
      {rec && <div className="mb-8"><p className="mb-2 text-sm font-bold uppercase tracking-wide text-saffron">{t("recommended")}</p><RecCard rec={rec} selectionId={undefined} /></div>}
      <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3" data-testid="scenario-grid">
        {data.scenarios.map((c) => (
          <li key={c.id} className="card flex flex-col p-5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="chip border-line bg-ivory-100 text-ink-muted" aria-label={`${t("difficulty")} ${c.difficulty} / 3`}>{t("difficulty")} {"●".repeat(c.difficulty)}{"○".repeat(3 - c.difficulty)}</span>
              {c.progress && c.progress.plays > 0 && <span className={`chip ${c.progress.best === "safe" ? "border-emerald/40 bg-emerald-100 text-emerald" : "border-saffron/40 bg-saffron-100 text-[#7a4b06]"}`}>{t("played")} ×{c.progress.plays}</span>}
              {c.recommended && <span className="chip border-saffron bg-saffron text-white">{t("recommended")}</span>}
            </div>
            <h2 className="mt-3 text-xl font-bold leading-tight text-midnight">{c.title}</h2>
            <p className="mt-1.5 flex-1 text-sm text-ink-muted">{c.tagline}</p>
            <p className="mt-3 text-xs text-ink-faint">{c.character.name}, {c.character.age} · {c.character.role}</p>
            <Link href={`/simulate/play?scenario=${c.id}`} className="btn-night mt-4" data-start={c.id}>{c.progress && c.progress.plays ? t("play_again") : t("start")} <Icon name="arrow" /></Link>
          </li>
        ))}
      </ul>
    </>
  );
}
