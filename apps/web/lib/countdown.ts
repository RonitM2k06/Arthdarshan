"use client";
import { useEffect, useRef, useState } from "react";

/** Pure helper (unit-tested): whole seconds left, never negative. */
export function remaining(startMs: number, nowMs: number, totalSeconds: number): number {
  return Math.max(0, Math.ceil(totalSeconds - (nowMs - startMs) / 1000));
}

export function useCountdown(totalSeconds: number | null, resetKey: string) {
  const start = useRef<number>(Date.now());
  const [left, setLeft] = useState<number | null>(totalSeconds);
  useEffect(() => {
    start.current = Date.now();
    setLeft(totalSeconds);
    if (!totalSeconds) return;
    const id = setInterval(() => setLeft(remaining(start.current, Date.now(), totalSeconds)), 250);
    return () => clearInterval(id);
  }, [totalSeconds, resetKey]);
  return { left, expired: totalSeconds != null && left === 0 };
}

export function formatClock(s: number): string {
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, "0")}`;
}
