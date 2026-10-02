"use client";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { SpeakButton } from "@/components/SpeakButton";
import { ErrorBox, Icon, Spinner } from "@/components/ui";
import { api } from "@/lib/api";
import { useApp } from "@/lib/state";

type Node = { id: string; name: string; category: string; simple: string; mastery: number | null };
type Graph = { nodes: Node[]; edges: { a: string; b: string }[] };
type Detail = { id: string; name: string; simple: string; detailed: string; examples: string[]; related: string[]; scenarios: string[]; simulation?: string | null; quiz_count: number;
  misconception_details: { id: string; name: string; correction: string }[] };

const CAT_COLOR: Record<string, string> = { basics: "#3A5FA0", core: "#C0841A", products: "#1F8F5F", rights: "#7A2432", safety: "#A8323E", behaviour: "#5b4b8a" };
const SCEN_NAME: Record<string, string> = { guaranteed_opportunity: "The Guaranteed Opportunity", whatsapp_expert: "The WhatsApp Expert", market_shock: "The Market Shock", one_basket: "Don't Put Everything in One Basket", hidden_fee: "The Hidden Fee", urgent_decision: "The Urgent Decision", confusing_document: "The Confusing Document", family_file: "The Family File" };

export function Concepts({ initial }: { initial?: string | null }) {
  const { t, lang } = useApp();
  const [g, setG] = useState<Graph | null>(null);
  const [sel, setSel] = useState<string | null>(initial ?? null);
  const [d, setD] = useState<Detail | null>(null);
  const [err, setErr] = useState(false);
  useEffect(() => { api<Graph>("/concepts").then(setG).catch(() => setErr(true)); }, [lang]);
  const load = useCallback((id: string) => { setSel(id); api<Detail>(`/concepts/${id}`).then(setD).catch(() => setErr(true)); }, []);
  useEffect(() => { if (sel) load(sel); }, [lang]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (initial) load(initial); }, [initial, load]);
  const layout = useMemo(() => {
    if (!g) return {} as Record<string, [number, number]>;
    const cats = Array.from(new Set(g.nodes.map((n) => n.category)));
    const pos: Record<string, [number, number]> = {};
    const cx = 330, cy = 250;
    g.nodes.sort((a, b) => cats.indexOf(a.category) - cats.indexOf(b.category));
    g.nodes.forEach((n, i) => { const a = -Math.PI / 2 + (i * 2 * Math.PI) / g.nodes.length; pos[n.id] = [cx + Math.cos(a) * 225, cy + Math.sin(a) * 195]; });
    return pos;
  }, [g]);
  if (err) return <ErrorBox />;
  if (!g) return <Spinner />;
  const nameOf = (id: string) => g.nodes.find((n) => n.id === id)?.name ?? id;
  return (
    <div className="grid gap-6 lg:grid-cols-[1.1fr_.9fr]">
      <div>
        <svg viewBox="0 0 660 500" className="card hidden w-full bg-white/60 md:block" role="group" aria-label="Concept graph">
          {g.edges.map((e, i) => { const [x1, y1] = layout[e.a] ?? [0, 0], [x2, y2] = layout[e.b] ?? [0, 0]; const on = sel && (e.a === sel || e.b === sel);
            return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={on ? "#B8740F" : "#DCD0B1"} strokeWidth={on ? 2.2 : 1} />; })}
          {g.nodes.map((n) => {
            const [x, y] = layout[n.id]; const on = sel === n.id; const m = n.mastery ?? 0;
            return (
              <g key={n.id} tabIndex={0} role="button" aria-label={`${n.name}${n.mastery != null ? `, ${t("mastery")} ${Math.round(m * 100)}%` : ""}`} aria-pressed={on} className="cursor-pointer outline-none"
                onClick={() => load(n.id)} onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && load(n.id)}>
                <circle cx={x} cy={y} r={on ? 27 : 23} fill="#fff" stroke={CAT_COLOR[n.category] ?? "#3A5FA0"} strokeWidth={on ? 4 : 2.5} />
                {n.mastery != null && <circle cx={x} cy={y} r={on ? 27 : 23} fill="none" stroke="#1F8F5F" strokeWidth="5" strokeDasharray={`${m * 2 * Math.PI * 23} 999`} transform={`rotate(-90 ${x} ${y})`} />}
                <text x={x} y={y + 40} textAnchor="middle" fontSize="11.5" fontWeight={on ? 700 : 500} fill="#1B2236">{n.name.length > 16 ? n.name.slice(0, 15) + "…" : n.name}</text>
              </g>
            );
          })}
        </svg>
        <ul className="flex flex-wrap gap-2 md:hidden" aria-label="Concepts">
          {g.nodes.map((n) => <li key={n.id}><button className={`chip !px-3 !py-2 text-sm ${sel === n.id ? "border-saffron bg-saffron-100" : "border-line bg-white"}`} onClick={() => load(n.id)}>{n.name}</button></li>)}
        </ul>
        <ul className="mt-3 flex flex-wrap gap-3 text-xs text-ink-muted" aria-label="Legend">
          {Object.entries(CAT_COLOR).map(([k, c]) => <li key={k} className="inline-flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-full" style={{ background: c }} />{k}</li>)}
          <li className="inline-flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-full border-2 border-emerald" />{t("mastery")}</li>
        </ul>
      </div>
      <aside className="card p-5" aria-live="polite" data-testid="concept-detail">
        {!d || !sel ? <p className="text-ink-muted">{t("tab_concepts")} — {g.nodes.length}</p> : (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-midnight">{d.name}</h2>
            <div><p className="eyebrow">{t("simple")}</p><p className="mt-1 text-lg">{d.simple}</p><div className="mt-2"><SpeakButton text={`${d.name}. ${d.simple}`} /></div></div>
            <div><p className="eyebrow">{t("detailed")}</p><p className="mt-1 text-ink-muted">{d.detailed}</p></div>
            {d.examples.length > 0 && <div><p className="eyebrow">{t("examples")}</p><ul className="mt-1 list-disc pl-5 text-ink-muted">{d.examples.map((e, i) => <li key={i}>{e}</li>)}</ul></div>}
            {d.misconception_details.length > 0 && <div><p className="eyebrow">{t("misconceptions")}</p><ul className="mt-1 space-y-2">{d.misconception_details.map((m) => <li key={m.id} className="rounded-lg border border-maroon/25 bg-maroon-100/40 p-2.5 text-sm"><b className="text-maroon">{m.id} · {m.name}</b><br />{m.correction}</li>)}</ul></div>}
            <div><p className="eyebrow">{t("related")}</p><div className="mt-1 flex flex-wrap gap-2">{d.related.map((r) => <button key={r} className="chip border-line bg-white hover:bg-ivory-100" onClick={() => load(r)}>{nameOf(r)}</button>)}</div></div>
            <div className="flex flex-wrap gap-2 border-t border-line pt-4">
              {d.scenarios.map((s) => <Link key={s} href={`/simulate/play?scenario=${s}`} className="btn-ghost !min-h-[40px] !py-1.5 text-sm"><Icon name="play" className="h-4 w-4" />{SCEN_NAME[s] ?? s}</Link>)}
              {d.simulation && <Link href={`/learn?tab=sims&sim=${d.simulation}`} className="btn-ghost !min-h-[40px] !py-1.5 text-sm">{t("tab_sims")}</Link>}
              {d.quiz_count > 0 && <Link href={`/learn?tab=quiz&concept=${d.id}`} className="btn-primary !min-h-[40px] !py-1.5 text-sm">{t("tab_quiz")}</Link>}
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
