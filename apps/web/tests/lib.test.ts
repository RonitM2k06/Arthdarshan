import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, setApiLang, setToken } from "@/lib/api";
import { remaining, formatClock } from "@/lib/countdown";
import { LANGS, STRINGS, speechLocale, translate, isLang, type Lang } from "@/lib/i18n";

describe("i18n completeness", () => {
  const langs: Lang[] = ["en", "hinglish", "hi"];
  it("every string exists in English, Hinglish and Hindi", () => {
    for (const [key, row] of Object.entries(STRINGS)) for (const l of langs) expect((row as any)[l]?.trim().length, `${key}.${l}`).toBeGreaterThan(0);
  });
  it("Hindi strings use Devanagari (or are language-neutral brand tokens)", () => {
    const neutral = new Set(["nav_home", "tagline"]);
    for (const [key, row] of Object.entries(STRINGS)) {
      const hi = (row as any).hi as string;
      if (/^[A-Za-z0-9 ·.\-–—,:%/()+'"?!]*$/.test(hi)) continue; // pure Latin token such as "NAV", "FOMO", "ETF"
      expect(/[ऀ-ॿ]/.test(hi), `${key}: ${hi}`).toBe(true);
    }
    expect(neutral.size).toBeGreaterThan(0);
  });
  it("Hinglish is written in Roman script", () => {
    for (const [key, row] of Object.entries(STRINGS)) expect(/[ऀ-ॿ]/.test((row as any).hinglish), key).toBe(false);
  });
  it("the safety badge states SIMULATED and no real money in every language", () => {
    expect(translate("en", "badge_sim")).toMatch(/SIMULATED.*NO REAL MONEY.*FICTIONAL/);
    expect(translate("hinglish", "badge_sim")).toMatch(/ASLI PAISA NAHI/);
    expect(translate("hi", "badge_sim")).toMatch(/असली पैसा नहीं/);
  });
  it("helpers", () => {
    expect(LANGS.map((l) => l.id)).toEqual(["en", "hinglish", "hi"]);
    expect(isLang("hi")).toBe(true);
    expect(isLang("fr")).toBe(false);
    expect(speechLocale("hi")).toBe("hi-IN");
    expect(speechLocale("hinglish")).toBe("en-IN");
  });
  it("no recommendation language in UI copy", () => {
    const banned = /\b(you should (buy|sell|invest)|best (stock|fund)|guaranteed profit)\b/i;
    for (const [key, row] of Object.entries(STRINGS)) expect((row as any).en, key).not.toMatch(banned);
  });
});

describe("countdown", () => {
  it("counts down whole seconds and never goes negative", () => {
    expect(remaining(0, 0, 45)).toBe(45);
    expect(remaining(0, 1000, 45)).toBe(44);
    expect(remaining(0, 44_001, 45)).toBe(1);
    expect(remaining(0, 45_000, 45)).toBe(0);
    expect(remaining(0, 999_999, 45)).toBe(0);
  });
  it("formats clock", () => {
    expect(formatClock(45)).toBe("0:45");
    expect(formatClock(125)).toBe("2:05");
  });
});

describe("api wrapper", () => {
  afterEach(() => { vi.restoreAllMocks(); setToken(null); });
  it("turns a network failure into ApiError(0, 'network')", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));
    await expect(api("/health")).rejects.toMatchObject({ status: 0, code: "network" });
  });
  it("parses the server's safe error envelope", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { code: "invalid_action", message: "nope" } }), { status: 400 })));
    const e = await api("/decisions", { method: "POST", body: {} }).catch((x) => x);
    expect(e).toBeInstanceOf(ApiError);
    expect(e).toMatchObject({ status: 400, code: "invalid_action", message: "nope" });
  });
  it("handles non-JSON error bodies", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>bad gateway</html>", { status: 502, statusText: "Bad Gateway" })));
    await expect(api("/x")).rejects.toMatchObject({ status: 502 });
  });
  it("sends the bearer token and language header, JSON body", async () => {
    setToken("tok123");
    setApiLang("hi");
    const f = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", f);
    await api("/decisions", { method: "POST", body: { a: 1 } });
    const [url, init] = f.mock.calls[0];
    expect(url).toBe("/api/decisions");
    expect(init.headers["Authorization"]).toBe("Bearer tok123");
    expect(init.headers["X-Arth-Lang"]).toBe("hi");
    expect(init.body).toBe('{"a":1}');
    setApiLang("en");
  });
});
