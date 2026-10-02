"use client";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { formatClock, useCountdown } from "@/lib/countdown";
import { startDictation, stopSpeaking, speak, type Recorder } from "@/lib/speech";
import { useApp } from "@/lib/state";
import type { Analysis, Card, DecisionResult, Pressure, StateView, Summary } from "@/lib/types";
import { SpeakButton } from "./SpeakButton";
import { Q_STYLE, SummaryView } from "./Summary";
import { ErrorBox, Icon, SimBadge, Spinner } from "./ui";

const PRESSURE_ICON: Record<string, string> = { urgency: "clock", countdown: "clock", scarcity: "alert", social_proof: "user", authority: "shield", fomo: "eye", fear: "alert", greed: "alert", loss_recovery: "alert", peer_pressure: "user", emotional_story: "alert" };

function Ring({ left, total }: { left: number; total: number }) {
  const r = 22, c = 2 * Math.PI * r, frac = total ? left / total : 0;
  return (
    <svg width="56" height="56" viewBox="0 0 56 56" role="img" aria-label={`${left} seconds left`}>
      <circle cx="28" cy="28" r={r} fill="none" stroke="#2B4380" strokeWidth="5" />
      <circle cx="28" cy="28" r={r} fill="none" stroke={left <= 10 ? "#E0737D" : "#E8C16A"} strokeWidth="5" strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c * (1 - frac)} transform="rotate(-90 28 28)" />
      <text x="28" y="33" textAnchor="middle" fontSize="14" fontWeight="700" fill="#FBF6EA">{left}</text>
    </svg>
  );
}

function PressureStrip({ items, countdown }: { items: Pressure[]; countdown: { left: number | null; total: number | null; expired: boolean } }) {
  const { t } = useApp();
  if (!items.length) return <p className="mt-4 text-sm text-ivory/70">{t("no_pressure")}</p>;
  return (
    <div className="mt-4 rounded-2xl border border-saffron-300/30 bg-midnight-700/60 p-3" data-testid="pressure">
      <div className="flex items-center gap-3">
        {countdown.total != null && countdown.left != null && <Ring left={countdown.left} total={countdown.total} />}
        <div className="min-w-0 flex-1">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-saffron-300">{t("pressure")}</p>
          <ul className="mt-1.5 flex flex-wrap gap-2">
            {items.map((p, i) => (
              <li key={i} className="chip border-saffron-300/40 bg-saffron-300/10 text-saffron-300" title={p.type}>
                <Icon name={PRESSURE_ICON[p.type] ?? "alert"} className="h-3.5 w-3.5" />
                <span className="text-ivory">{p.text}</span>
                <span aria-label={`intensity ${p.intensity} of 3`} className="ml-1 tracking-tighter">{"●".repeat(p.intensity)}<span className="opacity-30">{"●".repeat(3 - p.intensity)}</span></span>
              </li>
            ))}
          </ul>
        </div>
      </div>
      {countdown.total != null && <p className="mt-2 text-[0.7rem] text-ivory/60">{t("sim_timer_note")}</p>}
      {countdown.expired && <p role="status" className="mt-2 rounded-lg bg-danger-100/10 px-3 py-1.5 text-sm font-semibold text-[#f0a3a8]">{t("times_up")}</p>}
    </div>
  );
}

function Messages({ ch }: { ch: StateView["channel"] }) {
  if (ch.type === "none" || !ch.messages.length) return null;
  const initial = (ch.sender || "?").trim()[0]?.toUpperCase();
  return (
    <div className="mt-4 overflow-hidden rounded-2xl bg-ivory text-ink" data-testid="channel">
      <div className="flex items-center gap-2.5 border-b border-line bg-ivory-200 px-3 py-2">
        <span className="grid h-8 w-8 place-items-center rounded-full bg-midnight font-bold text-saffron-300" aria-hidden="true">{initial}</span>
        <span className="min-w-0"><span className="block truncate text-sm font-bold">{ch.sender || "—"}</span><span className="block text-[0.7rem] uppercase tracking-wide text-ink-faint">{ch.type}</span></span>
      </div>
      <div className="space-y-2 p-3">
        {ch.messages.map((m, i) => <p key={i} className="max-w-[92%] rounded-2xl rounded-tl-sm bg-white px-3.5 py-2 text-[0.95rem] leading-snug shadow-sm">{m}</p>)}
      </div>
    </div>
  );
}

function Evidence({ view, picked, toggle, locked, analysis }: { view: StateView; picked: Set<string>; toggle: (id: string) => void; locked: boolean; analysis: Analysis | null }) {
  const { t } = useApp();
  if (!view.evidence.length) return null;
  const rec = new Map((analysis?.evidence.recognized ?? []).map((e) => [e.id, e]));
  const mis = new Map((analysis?.evidence.missed ?? []).map((e) => [e.id, e]));
  const fa = new Map((analysis?.evidence.false_alarms ?? []).map((e) => [e.id, e]));
  return (
    <fieldset className="mt-5 min-w-0" disabled={locked && !analysis}>
      <legend className="mb-2 text-sm font-semibold text-ivory/90">{t("evidence_prompt")}</legend>
      <ul className="grid gap-2 sm:grid-cols-2">
        {view.evidence.map((e) => {
          const on = picked.has(e.id);
          const r = rec.get(e.id), m = mis.get(e.id), f = fa.get(e.id);
          const tone = analysis ? (r ? "border-emerald bg-emerald-100 text-ink" : m ? "border-saffron bg-saffron-100 text-ink" : "border-white/20 bg-white/5 text-ivory") : on ? "border-saffron-300 bg-saffron-300/20 text-ivory" : "border-white/20 bg-white/5 text-ivory hover:bg-white/10";
          return (
            <li key={e.id}>
              <button type="button" role="checkbox" aria-checked={on} disabled={!!analysis} onClick={() => toggle(e.id)} data-evidence={e.id}
                className={`w-full rounded-xl border px-3 py-2.5 text-left text-sm transition-colors ${tone}`}>
                <span className="flex items-start gap-2">
                  <span className={`mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded border ${on || r ? "border-current" : "border-white/40"}`} aria-hidden="true">{(on || r) && <Icon name="check" className="h-3.5 w-3.5" />}</span>
                  <span><span className="block font-semibold">{e.label}</span><span className={`block text-[0.8rem] ${analysis && (r || m) ? "text-ink-muted" : "text-ivory/75"}`}>{e.text}</span></span>
                </span>
                {analysis && (r || m) && <span className="mt-2 block border-t border-black/10 pt-2 text-[0.8rem] text-ink-muted"><b>{r ? "✓ " : "◦ "}</b>{(r || m)?.why}</span>}
                {analysis && f && !r && !m && <span className="mt-2 block border-t border-white/10 pt-2 text-[0.8rem] text-ivory/80">{f.why}</span>}
              </button>
            </li>
          );
        })}
      </ul>
    </fieldset>
  );
}

function Feedback({ res, onContinue, last }: { res: DecisionResult; onContinue: () => void; last: boolean }) {
  const { t } = useApp();
  const a = res.analysis;
  const resp = a.pressure_response === "held_steady" ? t("pressure_held") : a.pressure_response === "partly" ? t("pressure_partly") : a.pressure_response === "acted" ? t("pressure_acted") : null;
  return (
    <div className="space-y-4 anim animate-rise" aria-live="polite" data-testid="feedback">
      <div className="card bg-white p-4">
        <p className="eyebrow">{t("consequence")}</p>
        <p className="mt-1 font-serif text-xl font-semibold leading-snug text-midnight">{res.consequence}</p>
      </div>
      <div className="card bg-white p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="eyebrow">{t("analysis")}</p>
          <span className={`chip ${Q_STYLE[a.quality]}`}>{t(`q_${a.quality}` as any)}</span>
        </div>
        <p className="mt-2 text-[0.97rem]" data-testid="explanation">{a.explanation}</p>
        <p className="mt-1 text-[0.7rem] text-ink-faint">{t("explanation_by")}: {t("from_template")}{a.explanation_source === "llm" ? ` + ${t("from_llm")}` : ""}</p>
        <div className="mt-2"><SpeakButton text={a.explanation} /></div>
        {a.coach_note && <p className="mt-3 rounded-lg border border-midnight-600/30 bg-midnight/5 p-2.5 text-sm" data-testid="coach-note"><b className="block text-xs uppercase tracking-wide text-midnight-600">{t("coach_note")}</b>{a.coach_note}</p>}
        {resp && <p className="mt-3 rounded-lg bg-ivory-100 px-3 py-2 text-sm"><Icon name="clock" className="mr-1.5 inline h-4 w-4" />{resp}{a.latency_ms != null && ` · ${(a.latency_ms / 1000).toFixed(1)}s`}</p>}
        {a.behaviours.length > 0 && (
          <div className="mt-3"><p className="text-xs font-bold uppercase tracking-wide text-ink-muted">{t("patterns")}</p>
            <ul className="mt-1 space-y-2">{a.behaviours.slice(0, 2).map((b) => <li key={b.label} className="rounded-lg border border-line p-2.5"><p className={`text-xs font-bold ${b.positive ? "text-emerald" : "text-maroon"}`}>{b.name}</p><p className="text-sm text-ink-muted">{b.explanation}</p></li>)}</ul></div>
        )}
        {a.misconceptions.length > 0 && (
          <div className="mt-3"><p className="text-xs font-bold uppercase tracking-wide text-ink-muted">{t("misconceptions")}</p>
            <ul className="mt-1 space-y-2">{a.misconceptions.map((m) => <li key={m.id} className="rounded-lg border border-maroon/30 bg-maroon-100/50 p-2.5"><p className="text-xs font-bold text-maroon">{m.id} · {m.name}</p><p className="text-sm">{m.correction}</p></li>)}</ul></div>
        )}
        {a.safety.message && <p role="note" className="mt-3 rounded-lg border border-saffron/40 bg-saffron-100 p-2.5 text-sm"><Icon name="lock" className="mr-1.5 inline h-4 w-4" /><b>{t("safety_note")}:</b> {a.safety.message}</p>}
      </div>
      <button className="btn-primary w-full !py-3.5 text-base" onClick={onContinue} autoFocus data-testid="continue">{last ? t("reflection") : t("continue")} <Icon name="arrow" /></button>
    </div>
  );
}

export function Player({ scenarioId, selectionId }: { scenarioId: string; selectionId?: string | null }) {
  const { t, lang, simple, autoRead, user } = useApp();
  const [boot, setBoot] = useState<"loading" | "ready" | "error">("loading");
  const [err, setErr] = useState<string | undefined>();
  const [sessionId, setSessionId] = useState("");
  const [card, setCard] = useState<Card | null>(null);
  const [view, setView] = useState<StateView | null>(null);
  const [step, setStep] = useState(1);
  const [result, setResult] = useState<DecisionResult | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [action, setAction] = useState<string | null>(null);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [reasoning, setReasoning] = useState("");
  const [conf, setConf] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [showWhy, setShowWhy] = useState(false);
  const [showClues, setShowClues] = useState(false);
  const [mic, setMic] = useState<"idle" | "listening" | "processing">("idle");
  const [micNote, setMicNote] = useState<string | null>(null);
  const rec = useRef<Recorder | null>(null);
  const shownAt = useRef<number>(0);
  const started = useRef(false);

  const cdTotal = !simple ? view?.pressure.find((p) => p.countdown_seconds)?.countdown_seconds ?? null : null;
  const cd = useCountdown(cdTotal, `${sessionId}:${view?.id}`);

  const begin = useCallback(async () => {
    setBoot("loading");
    try {
      const j = await api<{ session_id: string; scenario: Card; state: StateView; step: number }>("/scenarios/start", { method: "POST", body: { scenario_id: scenarioId, selection_id: selectionId ? Number(selectionId) : null } });
      setSessionId(j.session_id); setCard(j.scenario); setView(j.state); setStep(j.step); setBoot("ready");
    } catch (e) {
      setErr(e instanceof ApiError && e.code !== "network" ? e.message : undefined);
      setBoot("error");
    }
  }, [scenarioId, selectionId]);

  useEffect(() => { if (user && !started.current) { started.current = true; void begin(); } }, [user, begin]);
  useEffect(() => { shownAt.current = performance.now(); }, [view?.id, sessionId]);
  useEffect(() => () => { stopSpeaking(); rec.current?.stop(); }, []);
  useEffect(() => { // optional: read each new situation aloud
    if ((autoRead || false) && view && !result && !summary) void speak(`${view.title}. ${view.narrative} ${view.channel.messages.join(" ")}`, lang);
  }, [view?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const submit = async () => {
    if (!view || !action || busy) return;
    setBusy(true); setConfirm(false); rec.current?.stop();
    const latency = Math.round(performance.now() - shownAt.current);
    try {
      const res = await api<DecisionResult>("/decisions", { method: "POST", body: { session_id: sessionId, state_key: view.id, action_id: action, reasoning, confidence: conf, latency_ms: latency, evidence_noticed: Array.from(picked), countdown_expired: cd.expired } });
      setResult(res);
      if (res.summary) setSummary(res.summary);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : undefined); setBoot("error");
    } finally { setBusy(false); }
  };

  const next = () => {
    if (!result) return;
    if (result.terminal) { window.scrollTo({ top: 0, behavior: "smooth" }); setResult(null); return; }
    setView(result.next_state!); setStep(result.step ?? step + 1);
    setResult(null); setAction(null); setPicked(new Set()); setReasoning(""); setConf(null); setShowWhy(false); setShowClues(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const toggleMic = async () => {
    setMicNote(null);
    if (mic === "listening") { rec.current?.stop(); return; }
    const r = await startDictation(lang, (text, final) => { setReasoning((prev) => (final ? (prev ? prev + " " : "") + text : prev)); }, (s, error) => {
      setMic(s);
      if (error) setMicNote(error === "unavailable" ? t("mic_unavailable") : error);
    });
    rec.current = r;
    if (!r) setMicNote(t("mic_unavailable"));
  };

  if (boot === "loading") return <Spinner />;
  if (boot === "error" || !view || !card) return <ErrorBox message={err} onRetry={() => { started.current = false; setErr(undefined); void begin(); }} />;

  if (summary && !result) return <SummaryView s={summary} />;

  const locked = !!result;
  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-5 lg:grid-cols-[1.15fr_.85fr]" data-testid="player" data-state={view.id}>
      <section aria-labelledby="scene-h" className="jali rounded-3xl bg-midnight p-5 text-ivory sm:p-7">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-saffron-300">{card.title} · {t("step")} {step}</p>
          <div className="flex items-center gap-2"><SimBadge short dark /><Link href="/simulate" className="text-xs text-ivory/70 underline">{t("quit")}</Link></div>
        </div>
        <p className="mt-2 text-sm text-ivory/75">{card.character.name}, {card.character.age} · {card.character.role}</p>
        <h1 id="scene-h" className="mt-3 text-3xl font-bold leading-tight sm:text-4xl">{view.title}</h1>
        <p className="mt-3 text-[1.05rem] leading-relaxed text-ivory/95" data-testid="narrative">{view.narrative}</p>
        <div className="mt-3"><SpeakButton text={`${view.title}. ${view.narrative} ${view.channel.messages.join(" ")}`} className="!border-ivory/30 !text-ivory hover:!bg-white/10" /></div>
        <Messages ch={view.channel} />
        <PressureStrip items={view.pressure} countdown={{ left: cd.left, total: cdTotal, expired: cd.expired }} />
        {simple && view.evidence.length > 0 && !showClues && !result ? (
          <button className="btn-light mt-5" onClick={() => setShowClues(true)}><Icon name="eye" /> {t("evidence")}</button>
        ) : (
          <Evidence view={view} picked={picked} locked={locked} analysis={result?.analysis ?? null} toggle={(id) => setPicked((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; })} />
        )}
        {view.simulation_hint && <Link href={`/learn?tab=sims&sim=${view.simulation_hint}`} className="mt-5 inline-block text-sm font-semibold text-saffron-300 underline">{t("see_sim")} →</Link>}
      </section>

      <section aria-label={t("actions_title")} className="lg:sticky lg:top-20 lg:self-start">
        {result ? <Feedback res={result} onContinue={next} last={result.terminal} /> : (
          <div className="card space-y-5 bg-white p-5 sm:p-6">
            <div>
              <h2 className="text-xl font-bold text-midnight">{t("actions_title")}</h2>
              <div role="radiogroup" aria-label={t("actions_title")} className="mt-3 space-y-2.5">
                {view.actions.map((a) => (
                  <button key={a.id} type="button" role="radio" aria-checked={action === a.id} data-action={a.id} onClick={() => setAction(a.id)}
                    className={`flex w-full items-center gap-3 rounded-xl border-2 px-4 py-3.5 text-left font-semibold transition-colors ${action === a.id ? "border-saffron bg-saffron-100 text-midnight" : "border-line bg-ivory hover:border-saffron-400 hover:bg-ivory-100"} ${simple ? "min-h-[72px] text-lg" : ""}`}>
                    <span className={`grid h-6 w-6 shrink-0 place-items-center rounded-full border-2 ${action === a.id ? "border-saffron bg-saffron text-white" : "border-line"}`} aria-hidden="true">{action === a.id && <Icon name="check" className="h-3.5 w-3.5" />}</span>
                    {a.label}
                  </button>
                ))}
              </div>
            </div>

            {simple && !showWhy ? (
              <button className="btn-ghost w-full" onClick={() => setShowWhy(true)}>+ {t("reasoning_label")}</button>
            ) : (
              <div>
                <label htmlFor="why" className="mb-1.5 block text-sm font-semibold text-midnight">{view.reasoning_prompt ? <>{view.reasoning_prompt} <span className="font-normal text-ink-faint">({lang === "en" ? "optional" : lang === "hi" ? "वैकल्पिक" : "zaroori nahi"})</span></> : t("reasoning_label")}</label>
                <div className="relative">
                  <textarea id="why" value={reasoning} onChange={(e) => setReasoning(e.target.value)} rows={3} maxLength={1200} placeholder={t("reasoning_ph")}
                    className="w-full resize-y rounded-xl border-2 border-line bg-white p-3 pr-14 text-[0.97rem] focus:border-saffron" />
                  <button type="button" onClick={toggleMic} aria-pressed={mic === "listening"} aria-label={mic === "listening" ? t("mic_listening") : t("mic")}
                    className={`absolute right-2 top-2 grid h-10 w-10 place-items-center rounded-full border ${mic === "listening" ? "animate-pulse border-danger bg-danger text-white" : "border-line bg-ivory text-midnight hover:bg-ivory-200"}`}>
                    <Icon name="mic" className="h-5 w-5" />
                  </button>
                </div>
                {mic !== "idle" && <p role="status" className="mt-1 text-xs text-ink-muted">{mic === "listening" ? t("mic_listening") : t("loading")}</p>}
                {micNote && <p role="status" className="mt-1 text-xs text-danger">{micNote}</p>}
              </div>
            )}

            <div>
              <p id="conf-l" className="mb-1.5 text-sm font-semibold text-midnight">{t("confidence")}</p>
              <div role="radiogroup" aria-labelledby="conf-l" className="flex items-center gap-2">
                <span className="text-xs text-ink-faint">{t("conf_low")}</span>
                {[1, 2, 3, 4, 5].map((n) => (
                  <button key={n} type="button" role="radio" aria-checked={conf === n} aria-label={`${n}`} onClick={() => setConf(n)} data-conf={n}
                    className={`grid h-11 w-11 place-items-center rounded-full border-2 font-bold ${conf === n ? "border-midnight bg-midnight text-saffron-300" : "border-line bg-ivory hover:bg-ivory-200"}`}>{n}</button>
                ))}
                <span className="text-xs text-ink-faint">{t("conf_high")}</span>
              </div>
            </div>

            <button className="btn-night w-full !py-3.5 text-base" disabled={!action || busy} onClick={() => (simple ? setConfirm(true) : void submit())} data-testid="decide">
              {busy ? t("loading") : action ? t("decide") : t("pick_action")} {action && !busy && <Icon name="arrow" />}
            </button>
          </div>
        )}
      </section>

      {confirm && (
        <div role="dialog" aria-modal="true" aria-labelledby="cf-h" className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4">
          <div className="card w-full max-w-md bg-white p-6 text-center">
            <h2 id="cf-h" className="text-2xl font-bold text-midnight">{t("confirm_title")}</h2>
            <p className="mt-3 rounded-xl bg-saffron-100 p-3 text-lg font-semibold">{view.actions.find((a) => a.id === action)?.label}</p>
            <div className="mt-5 grid gap-3">
              <button className="btn-night !min-h-[64px] text-lg" onClick={() => void submit()} autoFocus>{t("confirm_yes")}</button>
              <button className="btn-ghost !min-h-[64px] text-lg" onClick={() => setConfirm(false)}>{t("confirm_no")}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
