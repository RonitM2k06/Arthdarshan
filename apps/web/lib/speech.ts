// Voice helpers. Order of preference: local Piper TTS / faster-whisper STT (via the API) -> browser Web Speech API -> plain text.
import { api, getToken } from "./api";
import { speechLocale, type Lang } from "./i18n";

let audio: HTMLAudioElement | null = null;
let objectUrl: string | null = null;

export function stopSpeaking() {
  try {
    audio?.pause();
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = null;
    audio = null;
    if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
  } catch { /* ignore */ }
}

export type SpeakResult = "local" | "browser" | "unavailable";

export async function speak(text: string, lang: Lang, onEnd?: () => void): Promise<SpeakResult> {
  stopSpeaking();
  if (!text.trim()) return "unavailable";
  // 1) local neural TTS
  try {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    const tok = getToken();
    if (tok) headers["Authorization"] = `Bearer ${tok}`;
    const res = await fetch("/api/voice/tts", { method: "POST", headers, body: JSON.stringify({ text: text.slice(0, 1400), language: lang }) });
    if (res.ok) {
      const blob = await res.blob();
      objectUrl = URL.createObjectURL(blob);
      audio = new Audio(objectUrl);
      audio.onended = () => onEnd?.();
      await audio.play();
      return "local";
    }
  } catch { /* fall through */ }
  // 2) browser speech synthesis
  try {
    if ("speechSynthesis" in window) {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = speechLocale(lang);
      u.rate = 0.92;
      u.onend = () => onEnd?.();
      window.speechSynthesis.speak(u);
      return "browser";
    }
  } catch { /* fall through */ }
  return "unavailable";
}

export type Recorder = { stop: () => void };

/** Start dictation. Returns null if no microphone/recognition is available (caller shows a typing fallback). */
export async function startDictation(lang: Lang, onText: (text: string, final: boolean) => void, onState: (s: "listening" | "processing" | "idle", err?: string) => void): Promise<Recorder | null> {
  // Prefer local STT through MediaRecorder; fall back to the browser's recogniser.
  try {
    if (navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== "undefined") {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      const chunks: Blob[] = [];
      rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        onState("processing");
        try {
          const fd = new FormData();
          fd.append("audio", new Blob(chunks, { type: rec.mimeType || "audio/webm" }), "voice.webm");
          fd.append("language_hint", lang);
          const out = await api<{ text: string }>("/voice/transcribe", { method: "POST", form: fd });
          onText(out.text, true);
          onState("idle");
        } catch (e: any) {
          onState("idle", e?.message || "transcription failed");
        }
      };
      rec.start();
      onState("listening");
      return { stop: () => rec.state !== "inactive" && rec.stop() };
    }
  } catch { /* permission denied or no device -> try browser recogniser */ }
  const SR = (typeof window !== "undefined" && ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition)) || null;
  if (SR) {
    try {
      const r = new SR();
      r.lang = speechLocale(lang);
      r.interimResults = true;
      r.onresult = (e: any) => {
        const txt = Array.from(e.results).map((x: any) => x[0].transcript).join(" ");
        onText(txt, e.results[e.results.length - 1].isFinal);
      };
      r.onend = () => onState("idle");
      r.onerror = () => onState("idle", "speech recognition error");
      r.start();
      onState("listening");
      return { stop: () => r.stop() };
    } catch { /* fall through */ }
  }
  onState("idle", "unavailable");
  return null;
}
