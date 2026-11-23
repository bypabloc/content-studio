import type { TransitionType } from '../model/types';

// cspell:ignore fadeblack fadewhite wipeleft wiperight slideleft slideright circleopen: FFmpeg transition names.

export type TransitionWeights = { from: number; to: number; fill: number };

const TRANSITION_MODES: Record<TransitionType, number> = {
  fade: 1,
  fadeblack: 2,
  fadewhite: 3,
  wipeleft: 4,
  wiperight: 5,
  slideleft: 6,
  slideright: 7,
  circleopen: 8,
};

export function transitionMode(type: TransitionType): number {
  return TRANSITION_MODES[type];
}

export function transitionProgress(time: number, start: number, duration: number): number {
  return duration <= 0 ? 1 : Math.max(0, Math.min(1, (time - start) / duration));
}

/** Pesos alfa de los dos clips y del color de relleno en un punto del lienzo. */
export function transitionWeights(type: TransitionType, progress: number, x: number, y: number): TransitionWeights {
  const p = Math.max(0, Math.min(1, progress));
  if (type === 'fade') return { from: 1 - p, to: p, fill: 0 };
  if (type === 'fadeblack' || type === 'fadewhite') {
    const first = Math.max(0, 1 - 2 * p);
    const second = Math.max(0, 2 * p - 1);
    return { from: first, to: second, fill: 1 - first - second };
  }
  if (type === 'wipeleft') {
    const reveal = x < p;
    return { from: reveal ? 0 : 1, to: reveal ? 1 : 0, fill: 0 };
  }
  if (type === 'wiperight') {
    const reveal = x >= 1 - p;
    return { from: reveal ? 0 : 1, to: reveal ? 1 : 0, fill: 0 };
  }
  if (type === 'circleopen') {
    const reveal = Math.hypot(x - 0.5, y - 0.5) <= p * Math.SQRT1_2;
    return { from: reveal ? 0 : 1, to: reveal ? 1 : 0, fill: 0 };
  }
  return { from: 1, to: 1, fill: 0 };
}
