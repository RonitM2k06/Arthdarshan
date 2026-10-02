"use client";
import { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Concepts } from "@/components/learn/Concepts";
import { EvidenceLab, Quiz } from "@/components/learn/LabQuiz";
import { AskVoice, SafetyDemo, SimLab } from "@/components/learn/SimsAsk";
import { PageHead, Spinner } from "@/components/ui";
import { useApp } from "@/lib/state";
import type { StrKey } from "@/lib/i18n";

const TABS: { id: string; key: StrKey }[] = [
  { id: "concepts", key: "tab_concepts" }, { id: "lab", key: "tab_lab" }, { id: "sims", key: "tab_sims" },
  { id: "ask", key: "tab_ask" }, { id: "quiz", key: "tab_quiz" }, { id: "safety", key: "tab_safety" },
];

function Inner() {
  const { t } = useApp();
  const sp = useSearchParams();
  const tab = TABS.some((x) => x.id === sp.get("tab")) ? (sp.get("tab") as string) : "concepts";
  return (
    <>
      <PageHead eyebrow={t("nav_learn")} title={t("learn_title")} sub={t("illustrative")} />
      <div role="tablist" aria-label={t("learn_title")} className="mb-6 flex gap-1 overflow-x-auto border-b border-line pb-px">
        {TABS.map((x) => (
          <Link key={x.id} role="tab" aria-selected={tab === x.id} href={`/learn?tab=${x.id}`} scroll={false}
            className={`whitespace-nowrap rounded-t-xl px-4 py-2.5 text-sm font-semibold ${tab === x.id ? "border-x border-t border-line bg-white text-midnight" : "text-ink-muted hover:text-midnight"}`}>{t(x.key)}</Link>
        ))}
      </div>
      <div role="tabpanel">
        {tab === "concepts" && <Concepts initial={sp.get("concept")} />}
        {tab === "lab" && <EvidenceLab />}
        {tab === "sims" && <SimLab key={sp.get("sim") ?? "default"} initial={sp.get("sim")} />}
        {tab === "ask" && <AskVoice />}
        {tab === "quiz" && <Quiz concept={sp.get("concept")} />}
        {tab === "safety" && <SafetyDemo />}
      </div>
    </>
  );
}

export default function Learn() {
  return <Suspense fallback={<Spinner />}><Inner /></Suspense>;
}
