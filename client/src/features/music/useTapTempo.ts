import { useCallback, useRef } from 'react';

/** Se guardan los últimos 4 toques; con más de 2 s entre dos, el ritmo empieza de nuevo (spec 011, D-5). */
const KEEP = 4;
const RESET_MS = 2000;
const MIN_BPM = 30;
const MAX_BPM = 300;

/** BPM del promedio de los intervalos, o null si no hay dos toques o el ritmo sale de 30–300. */
function bpmOf(taps: number[]): number | null {
  if (taps.length < 2) return null;
  const average = (taps[taps.length - 1] - taps[0]) / (taps.length - 1);
  const bpm = Math.round(60000 / average);
  return bpm >= MIN_BPM && bpm <= MAX_BPM ? bpm : null;
}

/** Tap tempo: `tap(ms)` guarda el toque y devuelve el BPM actual. Los toques viven en una referencia, sin re-render. */
export function useTapTempo(): { tap: (now: number) => number | null } {
  const taps = useRef<number[]>([]);
  const tap = useCallback((now: number): number | null => {
    const last = taps.current[taps.current.length - 1];
    if (last !== undefined && now - last > RESET_MS) taps.current = [];
    taps.current = [...taps.current, now].slice(-KEEP);
    return bpmOf(taps.current);
  }, []);
  return { tap };
}
