"use client";
import { useEffect, useState } from "react";
import { Icon, Spinner } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { useApp } from "@/lib/state";

type LabRes = {
  signals_found: number; level: string; summary: string; note: string;
  questions: { id: string; question: string; answer: string; signals: { id: string; text: string; matched: string }[] }[];
  missing_information: { id: string; text: string }[]; verify_independently: { signal: string; action: string }[]; workflow: { step: string; text: string }[];
  safety: { redactions: string[]; message: string | null };
};

export function EvidenceLab() {
  const { t, lang } = useApp();
  const [samples, setSamples] = useState<{ id: string; title: string; text: string }[]>([]);
  const [text, setText] = useState("");
  const [res, setRes] = useState<LabRes | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { api<{ samples: any[] }>("/learning/evidence-lab/samples").then((r) => setSamples(r.samples)).catch(() => {}); }, []);
  const run = async (txt = text) => {
    if (!txt.trim()) return;
    setBusy(true); setErr(null);
    try { setRes(await api<LabRes>("/learning/evidence-lab/analyze", { method: "POST", body: { question: txt, language: lang } })); }
    catch (e) { setErr(e instanceof ApiError ? e.message : "error"); }
    finally { setBusy(false); }
  };
  return (
    <div className="space-y-6">
      <p className="max-w-3xl text-ink-muted">{t("lab_intro")}</p>
      <div className="card p-5">
        <div className="mb-3 flex flex-wrap gap-2" role="group" aria-label={t("try_these")}>
          {samples.map((s) => <button key={s.id} className="chip !px-3 !py-1.5 border-line bg-ivory-100 hover:bg-ivory-200" onClick={() => { setText(s.text); void run(s.text); }}>{s.title}</button>)}
        </div>
        <label htmlFor="claim" className="sr-only">Claim</label>
        <textarea id="claim" value={text} onChange={(e) => setText(e.target.value)} rows={4} maxLength={1500} placeholder="…" className="w-full rounded-xl border-2 border-line bg-white p-3" />
        <div className="mt-3 flex items-center gap-3"><button className="btn-night" onClick={() => void run()} disabled={busy || !text.trim()}><Icon name="eye" /> {busy ? t("loading") : t("analyse")}</button><span className="text-xs text-ink-faint">{t("badge_short")}</span></div>
        {err && <p role="alert" className="mt-2 text-danger">{err}</p>}
      </div>
      {res && (
        <div className="space-y-5 anim animate-rise" data-testid="lab-result">
          <div className={`card p-5 ${res.level === "many" ? "border-danger/50 bg-danger-100/60" : res.level === "several" ? "border-saffron/50 bg-saffron-100/60" : "bg-white"}`}>
            <p className="font-serif text-xl font-semibold text-midnight">{res.summary}</p>
            {res.safety.redactions.length > 0 && <p className="mt-2 text-sm text-maroon">{res.safety.message}</p>}
          </div>
          <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6" aria-label="Verification workflow">
            {res.workflow.map((w, i) => <li key={w.step} className="card p-3 text-center"><span className="mx-auto mb-1 grid h-7 w-7 place-items-center rounded-full bg-midnight text-sm font-bold text-saffron-300">{i + 1}</span><b className="block text-[0.7rem] tracking-wide text-saffron">{w.step}</b><span className="mt-1 block text-xs text-ink-muted">{w.text}</span></li>)}
          </ol>
          <div className="grid gap-5 lg:grid-cols-2">
            <section className="card p-5"><h3 className="text-lg font-bold text-midnight">{t("evidence")}</h3>
              <dl className="mt-3 space-y-3">{res.questions.map((q) => <div key={q.id}><dt className="font-semibold">{q.question}</dt><dd className="text-sm text-ink-muted">{q.answer}{q.signals.length > 0 && <span className="mt-1 block text-xs text-ink-faint">“{q.signals.map((s) => s.matched).join("”, “")}”</span>}</dd></div>)}</dl></section>
            <section className="card p-5"><h3 className="text-lg font-bold text-midnight">{t("missed")}</h3>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ink-muted">{res.missing_information.map((m) => <li key={m.id}>{m.text}</li>)}</ul>
              <h3 className="mt-5 text-lg font-bold text-midnight">{t("verify_next")}</h3>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ink-muted">{res.verify_independently.map((v, i) => <li key={i}>{v.action}</li>)}</ul></section>
          </div>
          <p className="text-xs text-ink-faint">{res.note}</p>
        </div>
      )}
    </div>
  );
}

type Q = { id: string; concept_id: string; question: string; options: string[] };
type QRes = { correct: boolean; correct_index: number; explanation: string; misconception: { id: string; name: string; correction: string } | null; mastery: number | null };

export function Quiz({ concept }: { concept?: string | null }) {
  const { t } = useApp();
  const [qs, setQs] = useState<Q[] | null>(null);
  const [i, setI] = useState(0);
  const [pick, setPick] = useState<number | null>(null);
  const [res, setRes] = useState<QRes | null>(null);
  const [t0, setT0] = useState(Date.now());
  const [score, setScore] = useState(0);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { api<{ questions: Q[] }>(`/learning/quiz?n=4${concept ? `&concept=${concept}` : ""}`).then((r) => { setQs(r.questions); setI(0); setScore(0); }).catch((e) => setErr(e.message)); }, [concept]);
  if (err) return <p role="alert" className="text-danger">{err}</p>;
  if (!qs) return <Spinner />;
  const q = qs[i];
  if (!q) return <div className="card p-6 text-center"><p className="font-serif text-2xl font-bold text-midnight">{score}/{qs.length}</p><button className="btn-night mt-4" onClick={() => location.reload()}>{t("retry")}</button></div>;
  const check = async () => {
    if (pick == null) return;
    const r = await api<QRes>("/learning/quiz/answer", { method: "POST", body: { question_id: q.id, selected_index: pick, latency_ms: Date.now() - t0 } });
    setRes(r); if (r.correct) setScore((s) => s + 1);
  };
  return (
    <div className="card max-w-2xl p-6" data-testid="quiz">
      <p className="eyebrow">{i + 1} / {qs.length}</p>
      <h3 className="mt-1 text-xl font-bold text-midnight">{q.question}</h3>
      <div role="radiogroup" aria-label={q.question} className="mt-4 space-y-2.5">
        {q.options.map((o, k) => {
          const show = res && (k === res.correct_index ? "border-emerald bg-emerald-100" : k === pick ? "border-danger bg-danger-100" : "border-line opacity-70");
          return <button key={k} role="radio" aria-checked={pick === k} disabled={!!res} onClick={() => setPick(k)} className={`w-full rounded-xl border-2 px-4 py-3 text-left font-medium ${show || (pick === k ? "border-saffron bg-saffron-100" : "border-line bg-ivory hover:bg-ivory-100")}`}>{o}</button>;
        })}
      </div>
      {res && (
        <div role="status" className="mt-4 rounded-xl bg-ivory-100 p-4">
          <p className={`font-bold ${res.correct ? "text-emerald" : "text-maroon"}`}>{res.correct ? t("correct") : t("not_quite")}</p>
          <p className="mt-1 text-sm">{res.explanation}</p>
          {res.misconception && <p className="mt-2 rounded-lg border border-maroon/30 bg-maroon-100/50 p-2.5 text-sm"><b className="text-maroon">{res.misconception.id} · {res.misconception.name}</b><br />{res.misconception.correction}</p>}
        </div>
      )}
      <div className="mt-5">{!res ? <button className="btn-night" disabled={pick == null} onClick={() => void check()}>{t("quiz_check")}</button>
        : <button className="btn-primary" onClick={() => { setI(i + 1); setPick(null); setRes(null); setT0(Date.now()); }}>{t("quiz_next")} <Icon name="arrow" /></button>}</div>
    </div>
  );
}
