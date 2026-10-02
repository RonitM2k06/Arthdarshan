"use client";
import { useMemo, useState } from "react";
import { useApp } from "@/lib/state";

// Fixed categorical order (validated palette: distinct for normal vision and colour-vision deficiencies when combined with
// the direct labels and legend below). Never cycled: more than 4 series fold into a table.
export const SERIES = ["#3A5FA0", "#C0841A", "#1F8F5F", "#A8323E"];

export type Series = { name: string; points: number[] };

const fmt = (v: number) => (v === 0 ? "0" : Math.abs(v) >= 1000 ? Math.round(v).toLocaleString("en-IN") : v >= 100 ? v.toFixed(0) : v.toFixed(1));

export function LineChart({ series, xLabel, yLabel, money = true, height = 300 }: { series: Series[]; xLabel: string; yLabel: string; money?: boolean; height?: number }) {
  const { t } = useApp();
  const [hover, setHover] = useState<number | null>(null);
  const [table, setTable] = useState(false);
  const shown = series.slice(0, 4);
  const W = 640, H = height, m = { l: 64, r: 90, t: 16, b: 38 };
  const n = Math.max(...shown.map((s) => s.points.length));
  const all = shown.flatMap((s) => s.points);
  const lo = Math.min(0, ...all), hi = Math.max(...all) || 1;
  const pad = (hi - lo) * 0.06;
  const y = (v: number) => m.t + (H - m.t - m.b) * (1 - (v - lo) / (hi + pad - lo));
  const x = (i: number) => m.l + (W - m.l - m.r) * (n <= 1 ? 0 : i / (n - 1));
  const ticks = useMemo(() => Array.from({ length: 5 }, (_, k) => lo + ((hi + pad - lo) * k) / 4), [lo, hi, pad]);
  const label = (v: number) => (money ? "₹" : "") + fmt(v);
  return (
    <figure className="m-0">
      <div className="mb-1 flex items-center justify-between text-xs text-ink-muted">
        <span>{yLabel}</span>
        <button className="underline" onClick={() => setTable(!table)} aria-pressed={table}>{t("show_table")}</button>
      </div>
      {!table ? (
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${yLabel} vs ${xLabel}: ${shown.map((s) => `${s.name} ends at ${label(s.points[s.points.length - 1])}`).join("; ")}`} className="w-full"
          onMouseLeave={() => setHover(null)}
          onMouseMove={(e) => {
            const r = (e.currentTarget as SVGSVGElement).getBoundingClientRect();
            const px = ((e.clientX - r.left) / r.width) * W;
            setHover(Math.min(n - 1, Math.max(0, Math.round(((px - m.l) / (W - m.l - m.r)) * (n - 1)))));
          }}>
          {ticks.map((tk, k) => (
            <g key={k}>
              <line x1={m.l} x2={W - m.r} y1={y(tk)} y2={y(tk)} stroke="#E7DDC3" strokeWidth="1" />
              <text x={m.l - 8} y={y(tk)} textAnchor="end" dominantBaseline="middle" fontSize="11" fill="#5B6580">{label(tk)}</text>
            </g>
          ))}
          <line x1={m.l} x2={W - m.r} y1={y(0)} y2={y(0)} stroke="#B9AB86" strokeWidth="1.2" />
          {Array.from({ length: Math.min(n, 8) }, (_, k) => Math.round((k * (n - 1)) / Math.max(Math.min(n, 8) - 1, 1))).map((i) => (
            <text key={i} x={x(i)} y={H - 14} textAnchor="middle" fontSize="11" fill="#5B6580">{i}</text>
          ))}
          <text x={(m.l + W - m.r) / 2} y={H - 1} textAnchor="middle" fontSize="11" fill="#5B6580">{xLabel}</text>
          {shown.map((s, k) => (
            <g key={s.name}>
              <polyline fill="none" stroke={SERIES[k]} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" points={s.points.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ")} />
              <text x={x(s.points.length - 1) + 8} y={y(s.points[s.points.length - 1])} dominantBaseline="middle" fontSize="11.5" fontWeight="600" fill="#1B2236">{s.name.length > 16 ? s.name.slice(0, 15) + "…" : s.name}</text>
            </g>
          ))}
          {hover != null && (
            <g pointerEvents="none">
              <line x1={x(hover)} x2={x(hover)} y1={m.t} y2={H - m.b} stroke="#0E1A33" strokeOpacity=".35" strokeDasharray="3 3" />
              {shown.map((s, k) => s.points[hover] != null && <circle key={k} cx={x(hover)} cy={y(s.points[hover])} r="4.5" fill={SERIES[k]} stroke="#fff" strokeWidth="2" />)}
              {(() => {
                const w = 190, h = 22 + shown.length * 17, tx = x(hover) > W / 2 ? x(hover) - w - 10 : x(hover) + 10;
                return (
                  <g>
                    <rect x={tx} y={m.t} width={w} height={h} rx="8" fill="#0E1A33" />
                    <text x={tx + 10} y={m.t + 16} fontSize="11.5" fill="#E8C16A" fontWeight="700">{xLabel} {hover}</text>
                    {shown.map((s, k) => <text key={k} x={tx + 10} y={m.t + 33 + k * 17} fontSize="11.5" fill="#FBF6EA"><tspan fill={SERIES[k]}>●</tspan> {s.name.slice(0, 18)}: {label(s.points[hover] ?? 0)}</text>)}
                  </g>
                );
              })()}
            </g>
          )}
        </svg>
      ) : (
        <div className="max-h-72 overflow-auto"><table className="w-full text-sm"><thead><tr className="text-left"><th>{xLabel}</th>{shown.map((s) => <th key={s.name}>{s.name}</th>)}</tr></thead>
          <tbody>{Array.from({ length: n }, (_, i) => <tr key={i} className="border-t border-line"><td>{i}</td>{shown.map((s) => <td key={s.name}>{s.points[i] != null ? label(s.points[i]) : "—"}</td>)}</tr>)}</tbody></table></div>
      )}
      <figcaption className="mt-2 flex flex-wrap gap-4 text-xs text-ink-muted">
        {shown.map((s, k) => <span key={s.name} className="inline-flex items-center gap-1.5"><i className="inline-block h-0.5 w-5" style={{ background: SERIES[k] }} />{s.name}</span>)}
      </figcaption>
    </figure>
  );
}

export type Bar = { label: string; value: number; extra?: any };

export function BarChart({ bars, yLabel, money = true, color = SERIES[0], highlightLast = false }: { bars: Bar[]; yLabel: string; money?: boolean; color?: string; highlightLast?: boolean }) {
  const { t } = useApp();
  const [hover, setHover] = useState<number | null>(null);
  const [table, setTable] = useState(false);
  const W = 640, H = 280, m = { l: 64, r: 12, t: 12, b: 58 };
  const hi = Math.max(...bars.map((b) => b.value), 1);
  const bw = (W - m.l - m.r) / bars.length;
  const y = (v: number) => m.t + (H - m.t - m.b) * (1 - v / hi);
  const label = (v: number) => (money ? "₹" : "") + fmt(v);
  return (
    <figure className="m-0">
      <div className="mb-1 flex items-center justify-between text-xs text-ink-muted">
        <span>{yLabel}</span>
        <button className="underline" onClick={() => setTable(!table)} aria-pressed={table}>{t("show_table")}</button>
      </div>
      {!table ? (
        <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-label={`${yLabel}: ${bars.map((b) => `${b.label} ${label(b.value)}`).join("; ")}`} className="w-full" onMouseLeave={() => setHover(null)}>
          {[0, 0.25, 0.5, 0.75, 1].map((f) => <g key={f}><line x1={m.l} x2={W - m.r} y1={y(hi * f)} y2={y(hi * f)} stroke="#E7DDC3" /><text x={m.l - 8} y={y(hi * f)} textAnchor="end" dominantBaseline="middle" fontSize="11" fill="#5B6580">{label(hi * f)}</text></g>)}
          {bars.map((b, i) => {
            const x0 = m.l + i * bw + bw * 0.18, w = bw * 0.64, top = y(b.value), h = Math.max(H - m.b - top, 0);
            const fill = highlightLast && i === bars.length - 1 ? "#A8323E" : color;
            return (
              <g key={i} onMouseEnter={() => setHover(i)} onFocus={() => setHover(i)} onBlur={() => setHover(null)} role="img" tabIndex={0} aria-label={`${b.label}: ${label(b.value)}`}>
                <rect x={m.l + i * bw} y={m.t} width={bw} height={H - m.t - m.b} fill="transparent" />
                <path d={`M${x0},${H - m.b} V${top + 4} Q${x0},${top} ${x0 + 4},${top} H${x0 + w - 4} Q${x0 + w},${top} ${x0 + w},${top + 4} V${H - m.b} Z`} fill={fill} opacity={hover == null || hover === i ? 1 : 0.55} />
                {h > 18 && bars.length <= 12 && <text x={x0 + w / 2} y={top - 5} textAnchor="middle" fontSize="11" fontWeight="600" fill="#1B2236">{label(b.value)}</text>}
                <text x={x0 + w / 2} y={H - m.b + 16} textAnchor="middle" fontSize="11" fill="#4C566E">{b.label.length > 14 ? b.label.slice(0, 13) + "…" : b.label}</text>
              </g>
            );
          })}
          {hover != null && (() => {
            const b = bars[hover], w = 170, tx = Math.min(Math.max(m.l + hover * bw + bw / 2 - w / 2, 4), W - w - 4);
            return <g pointerEvents="none"><rect x={tx} y={4} width={w} height={40} rx="8" fill="#0E1A33" /><text x={tx + 10} y={21} fontSize="11.5" fill="#E8C16A" fontWeight="700">{b.label.slice(0, 24)}</text><text x={tx + 10} y={36} fontSize="11.5" fill="#FBF6EA">{label(b.value)}{b.extra?.note ? ` — ${String(b.extra.note).slice(0, 30)}` : ""}</text></g>;
          })()}
        </svg>
      ) : (
        <table className="w-full text-sm"><thead><tr className="text-left"><th>#</th><th>{yLabel}</th></tr></thead><tbody>{bars.map((b, i) => <tr key={i} className="border-t border-line"><td>{b.label}</td><td>{label(b.value)}</td></tr>)}</tbody></table>
      )}
    </figure>
  );
}
