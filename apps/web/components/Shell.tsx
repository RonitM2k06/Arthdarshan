"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useApp } from "@/lib/state";
import { Wordmark } from "./Logo";
import { Icon, Spinner } from "./ui";
import { LANGS, type StrKey } from "@/lib/i18n";

const DESKTOP: { href: string; key: StrKey }[] = [
  { href: "/", key: "nav_home" },
  { href: "/simulate", key: "nav_simulate" },
  { href: "/learn", key: "nav_learn" },
  { href: "/resilience", key: "nav_resilience" },
  { href: "/progress", key: "nav_progress" },
  { href: "/settings", key: "nav_settings" },
];
const MOBILE: { href: string; key: StrKey; icon: string }[] = [
  { href: "/", key: "nav_home", icon: "home" },
  { href: "/simulate", key: "nav_simulate", icon: "play" },
  { href: "/learn", key: "nav_learn", icon: "book" },
  { href: "/resilience", key: "nav_resilience_short", icon: "shield" },
  { href: "/profile", key: "nav_profile", icon: "user" },
];

function active(path: string, href: string) {
  return href === "/" ? path === "/" : path === href || path.startsWith(href + "/");
}

function Prefs() {
  const { lang, setLang, simple, setSimple, t } = useApp();
  return (
    <div className="flex items-center gap-2">
      <label className="sr-only" htmlFor="lang-sel">{t("language")}</label>
      <select id="lang-sel" value={lang} onChange={(e) => void setLang(e.target.value as any)} className="max-w-[92px] rounded-lg border border-midnight-600 bg-midnight-800 px-1.5 py-1.5 text-xs font-semibold text-ivory sm:max-w-none sm:px-2">
        {LANGS.map((l) => <option key={l.id} value={l.id}>{l.native}</option>)}
      </select>
      <button onClick={() => void setSimple(!simple)} aria-pressed={simple} title={t("simple_mode")}
        className={`rounded-lg border px-2.5 py-1.5 text-xs font-bold ${simple ? "border-saffron-300 bg-saffron-300 text-midnight" : "border-midnight-600 text-ivory/85 hover:bg-midnight-700"}`}>
        Aa<span className="sr-only"> {t("simple_mode")}</span>
      </button>
    </div>
  );
}

export function Shell({ children }: { children: React.ReactNode }) {
  const { t, ready, serverDown, refresh } = useApp();
  const path = usePathname() || "/";
  const immersive = path.startsWith("/simulate/play");
  return (
    <>
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-midnight focus:px-4 focus:py-2 focus:text-ivory">
        {t("skip")}
      </a>
      <header className="sticky top-0 z-40 border-b border-midnight-700 bg-midnight text-ivory">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-2 px-3 py-2.5 sm:gap-4 sm:px-4">
          <Link href="/" aria-label="ARTHDARSHAN home">
            <Wordmark light />
          </Link>
          <nav aria-label="Primary" className="hidden items-center gap-1 md:flex">
            {DESKTOP.map((n) => (
              <Link
                key={n.href}
                href={n.href}
                aria-current={active(path, n.href) ? "page" : undefined}
                className={`rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${active(path, n.href) ? "bg-saffron-300 text-midnight" : "text-ivory/85 hover:bg-midnight-700"}`}
              >
                {t(n.key)}
              </Link>
            ))}
          </nav>
          <Prefs />
        </div>
      </header>
      {serverDown && (
        <div role="alert" className="bg-danger-100 px-4 py-3 text-center text-sm font-semibold text-danger">
          {t("err_server")}{" "}
          <button className="ml-2 underline" onClick={() => void refresh()}>
            {t("retry")}
          </button>
        </div>
      )}
      <main id="main" className={`mx-auto max-w-6xl px-4 ${immersive ? "py-4" : "py-8"} pb-28 md:pb-12`}>
        {ready ? children : <Spinner />}
      </main>
      <footer className="hidden border-t border-line bg-ivory-100 px-4 py-6 text-center text-xs text-ink-muted md:block">
        <p>
          {t("badge_sim")} · <Link className="underline" href="/privacy">{t("privacy")}</Link> · {t("offline_ok")}
        </p>
      </footer>
      <nav aria-label="Mobile" className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t border-midnight-700 bg-midnight text-ivory md:hidden">
        {MOBILE.map((n) => (
          <Link
            key={n.href}
            href={n.href}
            aria-current={active(path, n.href) ? "page" : undefined}
            className={`flex flex-col items-center gap-0.5 px-1 py-2 text-[0.7rem] font-semibold ${active(path, n.href) ? "text-saffron-300" : "text-ivory/75"}`}
          >
            <Icon name={n.icon} className="h-5 w-5" />
            {t(n.key)}
          </Link>
        ))}
      </nav>
    </>
  );
}
