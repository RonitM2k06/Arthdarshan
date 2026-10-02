"use client";
import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { Spinner } from "@/components/ui";
import { useApp } from "@/lib/state";

// One-click demo: fresh demo profile, straight into the hero scenario.
export default function Demo() {
  const { newProfile, t, ready } = useApp();
  const router = useRouter();
  const done = useRef(false);
  useEffect(() => {
    if (!ready || done.current) return;
    done.current = true;
    newProfile(true).then(() => router.replace("/simulate/play?scenario=guaranteed_opportunity&n=demo")).catch(() => router.replace("/simulate"));
  }, [ready, newProfile, router]);
  return <Spinner label={t("demo_title")} />;
}
