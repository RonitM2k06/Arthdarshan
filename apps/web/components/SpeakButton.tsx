"use client";
import { useEffect, useState } from "react";
import { speak, stopSpeaking } from "@/lib/speech";
import { useApp } from "@/lib/state";
import { Icon } from "./ui";

export function SpeakButton({ text, className = "", label }: { text: string; className?: string; label?: string }) {
  const { lang, t } = useApp();
  const [on, setOn] = useState(false);
  const [failed, setFailed] = useState(false);
  useEffect(() => () => stopSpeaking(), []);
  return (
    <span className="inline-flex items-center gap-2">
      <button
        type="button"
        className={`btn-ghost !min-h-[40px] !px-3 !py-1.5 text-sm ${className}`}
        aria-pressed={on}
        onClick={async () => {
          if (on) {
            stopSpeaking();
            setOn(false);
            return;
          }
          setOn(true);
          setFailed(false);
          const r = await speak(text, lang, () => setOn(false));
          if (r === "unavailable") {
            setOn(false);
            setFailed(true);
          }
        }}
      >
        <Icon name="speaker" className="h-4 w-4" /> {on ? t("stop") : label ?? t("read_aloud")}
      </button>
      {failed && <span role="status" className="text-xs text-ink-muted">Voice unavailable on this device — text only.</span>}
    </span>
  );
}
