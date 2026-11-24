/** Interpolación pura de keyframes. Espejo de server/src/content_studio/editor/keyframes.py. */

export type Ease = 'linear' | 'ease-in-out' | 'hold';
export type Keyframe = { t: number; value: number; ease: Ease };
export type KeyframeSegment = [t0: number, t1: number, v0: number, v1: number, ease: Ease];

/** Evalúa una propiedad en el tiempo relativo del clip; sin keyframes conserva `default`. */
export function valueAt(keyframes: Keyframe[], t: number, defaultValue: number): number {
  if (keyframes.length === 0) return defaultValue;
  if (t <= keyframes[0].t) return keyframes[0].value;
  for (let index = 0; index < keyframes.length - 1; index += 1) {
    const left = keyframes[index];
    const right = keyframes[index + 1];
    if (t >= right.t) continue;
    if (left.ease === 'hold') return left.value;
    let progress = (t - left.t) / (right.t - left.t);
    if (left.ease === 'ease-in-out') progress = 3 * progress ** 2 - 2 * progress ** 3;
    return left.value + (right.value - left.value) * progress;
  }
  return keyframes[keyframes.length - 1].value;
}

/** Expande keyframes en tramos hasta el fin del clip; el valor final se mantiene. */
export function segments(keyframes: Keyframe[], clipDuration: number): KeyframeSegment[] {
  if (keyframes.length === 0 || clipDuration <= 0) return [];
  const result: KeyframeSegment[] = [];
  const first = keyframes[0];
  if (first.t > 0) result.push([0, Math.min(first.t, clipDuration), first.value, first.value, 'hold']);
  for (let index = 0; index < keyframes.length - 1; index += 1) {
    const left = keyframes[index];
    const right = keyframes[index + 1];
    if (left.t >= clipDuration) break;
    const stop = Math.min(right.t, clipDuration);
    if (stop > left.t) result.push([left.t, stop, left.value, right.value, left.ease]);
  }
  const last = keyframes[keyframes.length - 1];
  if (last.t < clipDuration) result.push([Math.max(0, last.t), clipDuration, last.value, last.value, 'hold']);
  if (keyframes.length === 1 && result.length === 0) result.push([0, clipDuration, first.value, first.value, 'hold']);
  return result;
}
