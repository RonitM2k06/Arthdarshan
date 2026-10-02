"use client";
import Link from "next/link";
import { LANGS } from "@/lib/i18n";
import { PageHead, Icon } from "@/components/ui";
import { useApp } from "@/lib/state";

export default function Profile() {
  const { t, user, lang, setLang, simple, setSimple } = useApp();
  return (
    <div className="max-w-2xl space-y-6">
      <PageHead eyebrow={t("nav_profile")} title={user?.display_name || t("profile_title")} sub={t("profile_note")} />
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="card p-5"><p className="eyebrow">{t("streak")}</p><p className="font-serif text-4xl font-bold text-midnight">{user?.streak_days ?? 0}</p></div>
        <Link href="/progress" className="card flex items-center justify-between p-5 font-semibold text-midnight">{t("nav_progress")} <Icon name="arrow" /></Link>
      </div>
      <section className="card p-5"><h2 className="text-lg font-bold text-midnight">{t("language")}</h2>
        <div className="mt-3 flex flex-wrap gap-2" role="radiogroup" aria-label={t("language")}>{LANGS.map((l) => <button key={l.id} role="radio" aria-checked={lang === l.id} onClick={() => void setLang(l.id)} className={`chip !px-4 !py-2 text-sm ${lang === l.id ? "border-saffron bg-saffron-100" : "border-line bg-white"}`}>{l.native}</button>)}</div>
        <button className={`btn mt-4 w-full ${simple ? "border-emerald bg-emerald-100 text-emerald" : "btn-ghost"}`} aria-pressed={simple} onClick={() => void setSimple(!simple)}>{t("simple_mode")}: {simple ? t("yes") : t("no")}</button></section>
      <Link href="/settings" className="btn-ghost w-full"><Icon name="gear" /> {t("nav_settings")}</Link>
    </div>
  );
}
