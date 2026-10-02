"use client";
import { useState } from "react";
import { useApp } from "@/lib/state";

export type Dim = {
  id: string; name: string; short: string; score: number | null; n_observations: number; previous: number | null; change: number | null;
  evidence: { note: string; value: number }[]; measured: boolean;
};
export type FP = { dimensions: Dim[]; strengths: string[]; opportunities: string[]; summary: string; measured_count: number };

const C = { cur: "#3A5FA0", prev: "#C0841A", grid: "#DCD0B1", ink: "#4C566E" };

/** Polar chart of the ten dimensions. Unmeasured dimensions sit at the centre (hollow) instead of showing an invented number. */
export function Radar({ dims, showPrev = true, size = 440 }: { dims: Dim[]; showPrev?: boolean; size?: number }) {
  const { t } = useApp();
  const [hover, setHover] = useState<number | null>(null);
  const cx = size / 2, cy = size / 2, R = size / 2 - 64, n = dims.length;
  const ang = (i: number) => -Math.PI / 2 + (i * 2 * Math.PI) / n;
  const pt = (i: number, v: number) => [cx + Math.cos(ang(i)) * R * (v / 100), cy + Math.sin(ang(i)) * R * (v / 100)];
  const poly = (vals: (number | null)[]) => vals.map((v, i) => pt(i, v ?? 0).map((x) => x.toFixed(1)).join(",")).join(" ");
  const hasPrev = showPrev && dims.some((d) => d.previous != null);
  return (
    <figure className="m-0">
      <svg viewBox={`0 0 ${size} ${size}`} role="group" aria-label={dims.map((d) => `${d.name}: ${d.score ?? t("not_measured")}`).join(". ")} className="mx-auto w-full max-w-[460px]">
        {[25, 50, 75, 100].map((g) => (
          <polygon key={g} points={dims.map((_, i) => pt(i, g).join(",")).join(" ")} fill="none" stroke={C.grid} strokeWidth={g === 100 ? 1.4 : 1} />
        ))}
        {dims.map((_, i) => <line key={i} x1={cx} y1={cy} x2={pt(i, 100)[0]} y2={pt(i, 100)[1]} stroke={C.grid} strokeWidth="1" />)}
        {hasPrev && <polygon points={poly(dims.map((d) => d.previous))} fill={C.prev} fillOpacity=".08" stroke={C.prev} strokeWidth="2" strokeDasharray="5 4" />}
        <polygon points={poly(dims.map((d) => d.score))} fill={C.cur} fillOpacity=".16" stroke={C.cur} strokeWidth="2.4" strokeLinejoin="round" />
        {dims.map((d, i) => {
          const [x, y] = pt(i, d.score ?? 0);
          return (
            <g key={d.id} role="img" onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(i)} onBlur={() => setHover(null)} tabIndex={0}
              aria-label={`${d.name} ${d.score ?? t("not_measured")}`}>
              <circle cx={x} cy={y} r="11" fill="transparent" />
              <circle cx={x} cy={y} r={d.measured ? 5 : 4} fill={d.measured ? C.cur : "#fff"} stroke={d.measured ? "#fff" : C.cur} strokeWidth="2" />
            </g>
          );
        })}
        {dims.map((d, i) => {
          const [lx, ly] = pt(i, 122);
          const anchor = Math.abs(lx - cx) < 8 ? "middle" : lx > cx ? "start" : "end";
          return (
            <text key={d.id} x={lx} y={ly} textAnchor={anchor} dominantBaseline="middle" fontSize="12.5" fontWeight={hover === i ? 700 : 500} fill={hover === i ? "#0E1A33" : C.ink}>
              {d.short}{d.score != null ? ` ${Math.round(d.score)}` : ""}
            </text>
          );
        })}
        {hover != null && (() => {
          const d = dims[hover];
          const [x, y] = pt(hover, d.score ?? 0);
          const w = 190, h = 44, tx = Math.min(Math.max(x - w / 2, 4), size - w - 4), ty = y < size / 2 ? y + 14 : y - h - 14;
          return (
            <g pointerEvents="none">
              <rect x={tx} y={ty} width={w} height={h} rx="8" fill="#0E1A33" />
              <text x={tx + 10} y={ty + 18} fontSize="12" fill="#FBF6EA" fontWeight="700">{d.name}</text>
              <text x={tx + 10} y={ty + 35} fontSize="12" fill="#E8C16A">{d.score != null ? `${d.score} / 100 · ${d.n_observations} obs.` : t("not_measured")}</text>
            </g>
          );
        })()}
      </svg>
      <figcaption className="mt-1 flex flex-wrap items-center justify-center gap-5 text-xs text-ink-muted">
        <span className="inline-flex items-center gap-1.5"><i className="inline-block h-0.5 w-5" style={{ background: C.cur }} />{t("score")}</span>
        {hasPrev && <span className="inline-flex items-center gap-1.5"><i className="inline-block h-0.5 w-5 border-t-2 border-dashed" style={{ borderColor: C.prev }} />{t("previous")}</span>}
        <span className="inline-flex items-center gap-1.5"><i className="inline-block h-2.5 w-2.5 rounded-full border-2" style={{ borderColor: C.cur }} />{t("not_measured")}</span>
      </figcaption>
    </figure>
  );
}

export function DimRows({ dims }: { dims: Dim[] }) {
  const { t } = useApp();
  const [open, setOpen] = useState<string | null>(null);
  return (
    <ul className="divide-y divide-line rounded-2xl border border-line bg-white/70">
      {dims.map((d) => (
        <li key={d.id} className="px-4 py-3">
          <button type="button" className="flex w-full items-center gap-3 text-left" onClick={() => setOpen(open === d.id ? null : d.id)} aria-expanded={open === d.id}>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-semibold text-midnight">{d.name}</span>
              <span className="mt-1.5 block h-2 overflow-hidden rounded-full bg-ivory-200" aria-hidden="true">
                {d.score != null && <span className="block h-full rounded-full" style={{ width: `${d.score}%`, background: C.cur }} />}
              </span>
            </span>
            <span className="w-16 text-right">
              {d.score != null ? <span className="font-serif text-xl font-bold text-midnight">{Math.round(d.score)}</span> : <span className="text-xs text-ink-faint">{t("not_measured")}</span>}
            </span>
            <span className="w-14 text-right text-xs font-semibold" aria-label={d.change != null ? `${t("change")} ${d.change}` : undefined}>
              {d.change != null && d.change !== 0 ? (
                <span className={d.change > 0 ? "text-emerald" : "text-danger"}>{d.change > 0 ? "▲" : "▼"} {Math.abs(d.change).toFixed(1)}</span>
              ) : d.previous != null ? <span className="text-ink-faint">—</span> : null}
            </span>
          </button>
          {open === d.id && (
            <div className="mt-2 rounded-xl bg-ivory-100 p-3 text-sm text-ink-muted">
              <p className="mb-1 font-semibold text-ink">{t("evidence_behind")} {d.previous != null && <span className="font-normal">({t("previous")}: {Math.round(d.previous)})</span>}</p>
              {d.evidence.length ? <ul className="list-disc pl-5">{d.evidence.map((e, i) => <li key={i}>{e.note} <span className="text-ink-faint">({e.value})</span></li>)}</ul> : <p>{t("not_measured")}</p>}
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}

export function FingerprintCard({ fp, showPrev = true }: { fp: FP; showPrev?: boolean }) {
  const { t } = useApp();
  const [table, setTable] = useState(false);
  return (
    <section aria-labelledby="fp-h" className="card p-5 sm:p-7">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="fp-h" className="text-2xl font-bold text-midnight">{t("fp_title")}</h2>
        <button className="btn-ghost !min-h-[38px] !py-1 text-sm" onClick={() => setTable(!table)} aria-pressed={table}>{t("show_table")}</button>
      </div>
      <p className="mt-1 text-sm text-ink-muted">{t("fp_how")}</p>
      <p className="mt-3 rounded-xl bg-saffron-100 px-4 py-3 text-[0.95rem] font-medium text-[#5b3a05]" data-testid="fp-summary">{fp.summary}</p>
      <div className="mt-5 grid gap-6 lg:grid-cols-2">
        {!table ? <Radar dims={fp.dimensions} showPrev={showPrev} /> : (
          <table className="w-full text-sm">
            <caption className="sr-only">{t("fp_title")}</caption>
            <thead><tr className="text-left text-ink-muted"><th>#</th><th>{t("fp_title")}</th><th>{t("score")}</th><th>{t("previous")}</th><th>{t("change")}</th></tr></thead>
            <tbody>{fp.dimensions.map((d, i) => <tr key={d.id} className="border-t border-line"><td>{i + 1}</td><td>{d.name}</td><td>{d.score ?? "—"}</td><td>{d.previous ?? "—"}</td><td>{d.change ?? "—"}</td></tr>)}</tbody>
          </table>
        )}
        <DimRows dims={fp.dimensions} />
      </div>
    </section>
  );
}
