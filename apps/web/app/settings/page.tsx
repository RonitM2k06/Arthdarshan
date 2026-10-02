"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { PageHead } from "@/components/ui";
import { api, setToken } from "@/lib/api";
import { LANGS } from "@/lib/i18n";
import { useApp } from "@/lib/state";

function Switch({ checked, onChange, label, desc, id }: { checked: boolean; onChange: (v: boolean) => void; label: string; desc?: string; id: string }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div><label htmlFor={id} className="font-semibold text-midnight">{label}</label>{desc && <p className="text-sm text-ink-muted">{desc}</p>}</div>
      <button id={id} role="switch" aria-checked={checked} onClick={() => onChange(!checked)} className={`relative h-8 w-14 shrink-0 rounded-full border-2 transition-colors ${checked ? "border-emerald bg-emerald" : "border-line bg-ivory-200"}`}>
        <span className={`absolute top-0.5 h-6 w-6 rounded-full bg-white shadow transition-all ${checked ? "left-7" : "left-0.5"}`} />
        <span className="sr-only">{checked ? "on" : "off"}</span>
      </button>
    </div>
  );
}

export default function Settings() {
  const { t, lang, setLang, simple, setSimple, autoRead, setAutoRead, user, rename, signOut, refresh } = useApp();
  const [name, setName] = useState("");
  const [status, setStatus] = useState<any>(null);
  const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => { setName(user?.display_name ?? ""); }, [user?.display_name]);
  useEffect(() => { api("/models").then((m: any) => setStatus(m.components)).catch(() => setStatus(null)); }, []);
  const exportData = async () => {
    const data = await api("/users/me/export");
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    const a = document.createElement("a"); a.href = url; a.download = "arthdarshan-my-data.json"; a.click(); URL.revokeObjectURL(url);
  };
  const reset = async () => { if (confirm(t("confirm_reset"))) { await api("/users/me/data", { method: "DELETE" }); setMsg(t("done")); void refresh(); } };
  const del = async () => { if (confirm(t("confirm_reset"))) { await api("/users/me", { method: "DELETE" }); setToken(null); setMsg(t("done")); signOut(); } };
  const row = (k: string, ok: boolean, detail: string) => <li key={k} className="flex items-start gap-2 text-sm"><span className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${ok ? "bg-emerald" : "bg-saffron-400"}`} aria-hidden="true" /><span><b>{k}</b> — {ok ? "ready" : "fallback active"} <span className="text-ink-faint">({detail})</span></span></li>;
  return (
    <div className="max-w-3xl space-y-6">
      <PageHead eyebrow={t("nav_settings")} title={t("settings_title")} />
      <section className="card space-y-4 p-5" aria-labelledby="lang-h">
        <h2 id="lang-h" className="text-xl font-bold text-midnight">{t("language")}</h2>
        <div role="radiogroup" aria-labelledby="lang-h" className="grid gap-3 sm:grid-cols-3">
          {LANGS.map((l) => <button key={l.id} role="radio" aria-checked={lang === l.id} onClick={() => void setLang(l.id)} data-lang={l.id}
            className={`rounded-xl border-2 px-4 py-3 text-lg font-semibold ${lang === l.id ? "border-saffron bg-saffron-100" : "border-line bg-ivory hover:bg-ivory-100"}`}>{l.native}</button>)}
        </div>
      </section>
      <section className="card space-y-5 p-5" aria-labelledby="acc-h">
        <h2 id="acc-h" className="text-xl font-bold text-midnight">{t("simple_mode")}</h2>
        <Switch id="sw-simple" checked={simple} onChange={(v) => void setSimple(v)} label={t("simple_mode")} desc={t("simple_mode_desc")} />
        <Switch id="sw-read" checked={autoRead} onChange={setAutoRead} label={t("auto_read")} />
      </section>
      <section className="card space-y-3 p-5" aria-labelledby="name-h">
        <h2 id="name-h" className="text-xl font-bold text-midnight">{t("profile_title")}</h2>
        <label htmlFor="dn" className="text-sm text-ink-muted">{t("display_name")}</label>
        <div className="flex gap-2"><input id="dn" value={name} maxLength={40} onChange={(e) => setName(e.target.value)} className="min-h-[48px] flex-1 rounded-xl border-2 border-line bg-white px-4" /><button className="btn-night" onClick={() => void rename(name)}>{t("save")}</button></div>
        <p className="text-xs text-ink-faint">{t("profile_note")}</p>
      </section>
      <section className="card space-y-3 p-5" aria-labelledby="priv-h">
        <h2 id="priv-h" className="text-xl font-bold text-midnight">{t("privacy")}</h2>
        <Link href="/privacy" className="font-semibold underline">{t("privacy_page")}</Link>
        <div className="flex flex-wrap gap-3">
          <button className="btn-ghost" onClick={() => void exportData()}>{t("export_data")}</button>
          <button className="btn-ghost border-saffron text-[#7a4b06]" onClick={() => void reset()} data-testid="reset-data">{t("reset_data")}</button>
          <button className="btn-ghost border-danger text-danger" onClick={() => void del()}>{t("delete_profile")}</button>
        </div>
        {msg && <p role="status" className="font-semibold text-emerald">{msg}</p>}
      </section>
      {status && (
        <section className="card space-y-2 p-5" aria-labelledby="sys-h">
          <h2 id="sys-h" className="text-xl font-bold text-midnight">{t("system_status")}</h2>
          <ul className="space-y-1.5">
            {row("Core simulator", true, "deterministic engine, works offline")}
            {row("Local LLM", !!status.llm?.available, status.llm?.available ? status.llm.model : status.llm?.reason)}
            {row("Embeddings", !!status.embeddings?.loaded, status.embeddings?.loaded ? "hybrid retrieval" : "keyword retrieval")}
            {row("Speech-to-text", !!status.stt?.available, status.stt?.available ? "faster-whisper (local)" : "browser speech or typing")}
            {row("Text-to-speech", !!status.tts?.available, status.tts?.available ? "Piper (local)" : "browser speech")}
            {row("ML classifiers", !!status.ml?.misconception_clf, status.ml?.misconception_clf ? "trained locally" : "rules only")}
          </ul>
        </section>
      )}
    </div>
  );
}
