"use client";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, ApiError, getToken, setApiLang, setToken, startProfile } from "./api";
import { isLang, translate, type Lang, type StrKey } from "./i18n";

export type User = { public_id: string; display_name: string | null; language: Lang; simple_mode: boolean; is_demo: boolean; streak_days: number };

type Ctx = {
  user: User | null;
  lang: Lang;
  simple: boolean;
  autoRead: boolean;
  ready: boolean;
  serverDown: boolean;
  t: (k: StrKey) => string;
  setLang: (l: Lang) => Promise<void>;
  setSimple: (v: boolean) => Promise<void>;
  setAutoRead: (v: boolean) => void;
  refresh: () => Promise<void>;
  newProfile: (demo?: boolean) => Promise<User>;
  rename: (n: string) => Promise<void>;
  signOut: () => void;
};

const AppCtx = createContext<Ctx | null>(null);
const LS = { lang: "arth.lang", simple: "arth.simple", read: "arth.autoread" };

function ls(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}
function lsSet(key: string, v: string) {
  try {
    localStorage.setItem(key, v);
  } catch {
    /* ignore */
  }
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [lang, setLangState] = useState<Lang>("en");
  const [simple, setSimpleState] = useState(false);
  const [autoRead, setAutoReadState] = useState(false);
  const [ready, setReady] = useState(false);
  const [serverDown, setServerDown] = useState(false);

  const applyPrefs = useCallback((l: Lang, s: boolean) => {
    setLangState(l);
    setSimpleState(s);
    setApiLang(l);
    document.documentElement.lang = l === "hi" ? "hi" : l === "hinglish" ? "en-IN" : "en";
    document.documentElement.dataset.simple = s ? "true" : "false";
    lsSet(LS.lang, l);
    lsSet(LS.simple, String(s));
  }, []);

  const init = useCallback(async () => {
    const storedLang = ls(LS.lang);
    const l: Lang = isLang(storedLang) ? storedLang : "en";
    const s = ls(LS.simple) === "true";
    applyPrefs(l, s);
    setAutoReadState(ls(LS.read) === "true");
    try {
      let me: User | null = null;
      if (getToken()) {
        try {
          me = await api<User>("/users/me");
        } catch (e) {
          if (e instanceof ApiError && e.status === 401) setToken(null);
          else throw e;
        }
      }
      const u: User = me ?? (await startProfile(l, s));
      setUser(u);
      applyPrefs(u.language, u.simple_mode);
      setServerDown(false);
    } catch (e) {
      if (e instanceof ApiError && e.status === 0) setServerDown(true);
    } finally {
      setReady(true);
    }
  }, [applyPrefs]);

  useEffect(() => {
    void init();
  }, [init]);

  const setLang = useCallback(async (l: Lang) => {
    applyPrefs(l, simple);
    try {
      if (user) setUser(await api<User>("/users/me", { method: "PATCH", body: { language: l } }));
    } catch { /* offline: preference still applies locally */ }
  }, [applyPrefs, simple, user]);

  const setSimple = useCallback(async (v: boolean) => {
    applyPrefs(lang, v);
    try {
      if (user) setUser(await api<User>("/users/me", { method: "PATCH", body: { simple_mode: v } }));
    } catch { /* ignore */ }
  }, [applyPrefs, lang, user]);

  const value = useMemo<Ctx>(() => ({
    user, lang, simple, autoRead, ready, serverDown,
    t: (k) => translate(lang, k),
    setLang, setSimple,
    setAutoRead: (v) => { setAutoReadState(v); lsSet(LS.read, String(v)); },
    refresh: init,
    newProfile: async (demo = false) => { const u = await startProfile(lang, simple, demo); setUser(u); return u; },
    rename: async (n) => { setUser(await api<User>("/users/me", { method: "PATCH", body: { display_name: n.trim() || null } })); },
    signOut: () => { setToken(null); setUser(null); void init(); },
  }), [user, lang, simple, autoRead, ready, serverDown, setLang, setSimple, init]);

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}

export function useApp(): Ctx {
  const c = useContext(AppCtx);
  if (!c) throw new Error("useApp must be used inside AppProvider");
  return c;
}
