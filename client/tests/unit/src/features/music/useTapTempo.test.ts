import { renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { useTapTempo } from '@/features/music/useTapTempo';

/** Toca en esos instantes (ms) y devuelve el BPM tras el último toque. */
function tapAt(times: number[]): number | null {
  const { result } = renderHook(() => useTapTempo());
  let bpm: number | null = null;
  for (const at of times) bpm = result.current.tap(at);
  return bpm;
}

describe('useTapTempo (spec 011, D-5, AC-7)', () => {
  it('WHEN se dan 4 toques cada 500 ms THEN el BPM queda en 120', () => {
    expect(tapAt([0, 500, 1000, 1500])).toBe(120);
  });

  it('WHEN hay un solo toque THEN todavía no hay BPM', () => {
    expect(tapAt([0])).toBeNull();
  });

  it('WHEN pasan más de 2 s entre toques THEN empieza de nuevo', () => {
    expect(tapAt([0, 500, 5000])).toBeNull();
    expect(tapAt([0, 500, 5000, 5500])).toBe(120);
  });

  it('WHEN hay más de 4 toques THEN promedia solo los últimos 4', () => {
    expect(tapAt([0, 1000, 1500, 2000, 2500])).toBe(120);
  });

  it('WHEN el ritmo sale de 30–300 BPM THEN no hay BPM', () => {
    expect(tapAt([0, 100])).toBeNull();
  });
});
