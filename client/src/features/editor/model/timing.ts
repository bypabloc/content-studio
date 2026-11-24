/** Mapeo entre el tiempo de fuente y el tiempo del timeline con velocidad constante. */

const MIN_SPEED = 0.25;
const MAX_SPEED = 4;

/** Duración del clip en el timeline; proyectos v2 sin velocidad usan uno. */
export function clipDuration(clip: { src_in: number; src_out: number; speed?: number }): number {
  return (clip.src_out - clip.src_in) / speedOf(clip.speed ?? 1);
}

/** Mapea un tiempo absoluto del timeline al tiempo absoluto de la fuente. */
export function sourceTime(clip: { src_in: number; start: number; speed?: number }, timelineTime: number): number {
  return clip.src_in + (timelineTime - clip.start) * speedOf(clip.speed ?? 1);
}

/** Divide la velocidad en filtros atempo dentro del rango admitido por FFmpeg. */
export function atempoFilters(speed: number): string[] {
  let remaining = speedOf(speed);
  const factors: number[] = [];
  while (remaining < 0.5) {
    factors.push(0.5);
    remaining /= 0.5;
  }
  while (remaining > 2) {
    factors.push(2);
    remaining /= 2;
  }
  if (Math.abs(remaining - 1) > 1e-12) factors.push(remaining);
  return factors.map((factor) => `atempo=${factor}`);
}

function speedOf(value: number): number {
  if (!Number.isFinite(value) || value < MIN_SPEED || value > MAX_SPEED) throw new Error('invalid speed');
  return value;
}
