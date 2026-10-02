"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { api, setToken } from "@/lib/api";
import { useEffect, useRef } from "react";
import { Spinner } from "@/components/ui";
import { useApp } from "@/lib/state";

// One-click demo: fresh demo profile, straight into the hero scenario.
function Inner() {
  const { newProfile, t, ready, lang, refresh } = useApp();
  const router = useRouter();
  const persona = useSearchParams().get("persona");
  const done = useRef(false);
  useEffect(() => {
    if (!ready || done.current) return;
    done.current = true;
    if (persona) {
      api<{ token: string }>("/auth/demo-persona", { method: "POST", body: { language: lang } }).then(async (r) => { setToken(r.token); await refresh(); router.replace("/resilience"); }).catch(() => router.replace("/simulate"));
      return;
    }
    newProfile(true).then(() => router.replace("/simulate/play?scenario=guaranteed_opportunity&n=demo")).catch(() => router.replace("/simulate"));
  }, [ready, newProfile, router, persona, lang, refresh]);
  return <Spinner label={t("demo_title")} />;
}

export default function Demo() {
  return (
    <Suspense fallback={<Spinner />}>
      <Inner />
    </Suspense>
  );
}
