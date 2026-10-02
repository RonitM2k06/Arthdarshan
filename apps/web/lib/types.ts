import type { FP } from "@/components/Fingerprint";

export type Pressure = { type: string; text: string; countdown_seconds?: number | null; intensity: number };
export type Evidence = { id: string; label: string; text: string };
export type StateView = {
  id: string; title: string; narrative: string; reasoning_prompt?: string | null; simulation_hint?: string | null; terminal: boolean; disclaimer: string;
  channel: { type: string; sender: string | null; messages: string[] };
  pressure: Pressure[]; evidence: Evidence[]; actions: { id: string; label: string }[];
};
export type Card = {
  id: string; title: string; tagline: string; difficulty: number; character: { name: string; age: number; role: string };
  concept_tags: string[]; pressure_tags: string[]; disclaimer: string; progress?: { plays: number; best: string | null; last: string | null }; recommended?: boolean;
};
export type EvItem = { id: string; label: string; why: string | null };
export type Analysis = {
  quality: "safe" | "mixed" | "unsafe"; explanation: string; explanation_source: "llm" | "template"; coach_note: string | null;
  evidence: { recall: number | null; recognized: EvItem[]; missed: EvItem[]; false_alarms: EvItem[] };
  behaviours: { label: string; name: string; positive: boolean; explanation: string; confidence: number; source: string }[];
  misconceptions: { id: string; name: string; correction: string; source: string; confidence: number }[];
  pressure: { type: string; text: string }[]; pressure_response: "held_steady" | "partly" | "acted" | null;
  latency_ms: number | null; countdown_expired: boolean; emotions: string[]; uncertainty_recognized: boolean;
  safety: { flags: string[]; message: string | null; redactions: string[] };
};
export type Rec = { kind: string; id: string; title: string; difficulty: number | null; rationale: string; reasons: string[]; predicted_success: number | null; mastery_estimate: number | null };
export type Next = { scenario: Rec | null; alternatives: Rec[]; other_training: Rec[]; selection_id?: number; model: string };
export type Summary = {
  scenario_id: string; title: string; disclaimer: string;
  outcome: { kind: "safe" | "mixed" | "unsafe"; headline: string; summary: string; simulated_loss?: number | null };
  decisions: { state: string; action: string; quality: "safe" | "mixed" | "unsafe"; latency_s: number | null; confidence: number | null }[];
  evidence: { recognized: (EvItem & { state: string })[]; missed: (EvItem & { state: string })[]; recall: number | null; requested_verification: number };
  pressure: { decisions_under_pressure: number; held_steady: number; acted_under_pressure: number; types: string[]; countdown_expired: number };
  decision_speed: { avg_s: number | null; fastest_s: number | null; slowest_s: number | null };
  behaviours: { label: string; name: string; positive: boolean; explanation: string; count: number }[];
  misconceptions: { id: string; name: string; correction: string; source: string }[];
  misconceptions_resolved: { id: string; name: string; correction: string }[];
  micro_lesson: { concept_id: string; title: string; body: string };
  reflection: { key_points: string[]; questions: string[] };
  fingerprint: FP; next: Next;
};
export type DecisionResult = { decision_id: number; consequence: string; analysis: Analysis; terminal: boolean; next_state?: StateView; step?: number; summary?: Summary };
