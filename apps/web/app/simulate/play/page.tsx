"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Player } from "@/components/Player";
import { Spinner } from "@/components/ui";

function Inner() {
  const sp = useSearchParams();
  const scenario = sp.get("scenario") || "guaranteed_opportunity";
  // key forces a fresh session when the scenario changes
  return <Player key={`${scenario}:${sp.get("sel") ?? ""}:${sp.get("n") ?? ""}`} scenarioId={scenario} selectionId={sp.get("sel")} />;
}

export default function PlayPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <Inner />
    </Suspense>
  );
}
