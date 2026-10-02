export function Mark({ size = 34 }: { size?: number }) {
  // An eight-pointed star (a nod to jali lattice work) around an "observatory" eye.
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true" focusable="false">
      <path d="M24 2l5.2 12.6L42 20l-12.8 5.4L24 46l-5.2-20.6L6 20l12.8-5.4z" fill="#0E1A33" />
      <path d="M24 2l5.2 12.6L42 20l-12.8 5.4L24 46l-5.2-20.6L6 20l12.8-5.4z" fill="none" stroke="#E8C16A" strokeWidth="1.2" />
      <circle cx="24" cy="23" r="6.2" fill="none" stroke="#E8C16A" strokeWidth="1.6" />
      <circle cx="24" cy="23" r="2.4" fill="#D79B2E" />
    </svg>
  );
}

export function Wordmark({ light = false }: { light?: boolean }) {
  return (
    <span className="flex items-center gap-2">
      <Mark size={30} />
      <span className={`font-serif text-[0.95rem] font-bold tracking-[0.08em] sm:text-[1.15rem] sm:tracking-[0.14em] ${light ? "text-ivory" : "text-midnight"}`}>ARTHDARSHAN</span>
    </span>
  );
}
