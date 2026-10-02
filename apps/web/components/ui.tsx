"use client";
import { useApp } from "@/lib/state";

export function SimBadge({ short = false, dark = false }: { short?: boolean; dark?: boolean }) {
  const { t } = useApp();
  return (
    <span role="note" className={`chip ${dark ? "border-saffron-300/60 bg-saffron-300/10 text-saffron-300" : "border-saffron/50 bg-saffron-100 text-[#7a4b06]"}`}>
      <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="5" fill="none" stroke="currentColor" strokeWidth="1.4" /><path d="M6 3v3.4l2 1.2" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round" /></svg>
      {short ? t("badge_short") : t("badge_sim")}
    </span>
  );
}

export function Spinner({ label }: { label?: string }) {
  const { t } = useApp();
  return (
    <div role="status" aria-live="polite" className="flex items-center justify-center gap-3 py-16 text-ink-muted">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-saffron border-t-transparent" />
      <span>{label ?? t("loading")}</span>
    </div>
  );
}

export function ErrorBox({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  const { t } = useApp();
  return (
    <div role="alert" className="card mx-auto my-8 max-w-xl border-danger/40 bg-danger-100 p-6 text-center">
      <p className="font-semibold text-danger">{message || t("err_generic")}</p>
      {onRetry && <button className="btn-ghost mt-4" onClick={onRetry}>{t("retry")}</button>}
    </div>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="card border-dashed bg-ivory-100/60 p-8 text-center text-ink-muted">{children}</div>;
}

export function PageHead({ eyebrow, title, sub, right }: { eyebrow?: string; title: string; sub?: string; right?: React.ReactNode }) {
  return (
    <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div className="max-w-2xl">
        {eyebrow && <p className="eyebrow mb-1">{eyebrow}</p>}
        <h1 className="text-3xl font-bold text-midnight sm:text-4xl">{title}</h1>
        {sub && <p className="mt-2 text-ink-muted">{sub}</p>}
      </div>
      {right}
    </header>
  );
}

const PATHS: Record<string, string> = {
  home: "M3 11l9-8 9 8M5 10v10h5v-6h4v6h5V10",
  play: "M6 4l14 8-14 8z",
  book: "M4 5a2 2 0 012-2h12v16H6a2 2 0 00-2 2zM4 19a2 2 0 012-2h12",
  shield: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z",
  chart: "M4 20V10M10 20V4M16 20v-8M22 20H2",
  user: "M12 12a4 4 0 100-8 4 4 0 000 8zM4 21a8 8 0 0116 0",
  gear: "M12 15a3 3 0 100-6 3 3 0 000 6zM19 12l2-1-2-4-2 .5a7 7 0 00-1.6-1L15 4h-4l-.4 2.5a7 7 0 00-1.6 1L7 7l-2 4 2 1a7 7 0 000 2l-2 1 2 4 2-.5a7 7 0 001.6 1L11 20h4l.4-2.5a7 7 0 001.6-1l2 .5 2-4-2-1a7 7 0 000-2z",
  speaker: "M4 9v6h4l5 4V5L8 9zM16 8a5 5 0 010 8",
  mic: "M12 3a3 3 0 00-3 3v6a3 3 0 006 0V6a3 3 0 00-3-3zM6 11a6 6 0 0012 0M12 17v4",
  check: "M5 12l5 5L20 7",
  x: "M6 6l12 12M18 6L6 18",
  alert: "M12 4l9 16H3zM12 10v4M12 17v.5",
  eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12zM12 15a3 3 0 100-6 3 3 0 000 6z",
  clock: "M12 21a9 9 0 100-18 9 9 0 000 18zM12 7v5l3 2",
  arrow: "M5 12h14M13 6l6 6-6 6",
  lock: "M6 11V8a6 6 0 0112 0v3M5 11h14v10H5z",
};

export function Icon({ name, className = "h-5 w-5" }: { name: string; className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d={PATHS[name] ?? PATHS.check} />
    </svg>
  );
}
