/**
 * Geometría y selección de la línea de tiempo (spec 017, AC-7). Funciones puras: la pantalla convierte el tiempo en
 * píxeles con la escala del zoom, y mueve la selección con `apply` (así el «sin pisar» es el mismo del servidor).
 */

import { apply } from './ops';
import { clipLength } from './validate';
import type { Clip, Doc } from './types';

/** Píxeles por segundo de cada nivel de zoom, de más lejos a más cerca. */
export const ZOOM_LEVELS = [5, 10, 20, 40, 80, 160, 320] as const;

/** El siguiente nivel de zoom hacia adentro; en el último se queda. */
export function zoomIn(pxPerSecond: number): number {
  const index = ZOOM_LEVELS.indexOf(pxPerSecond as (typeof ZOOM_LEVELS)[number]);
  return ZOOM_LEVELS[Math.min(index + 1, ZOOM_LEVELS.length - 1)];
}

/** El nivel de zoom hacia afuera; en el primero se queda. */
export function zoomOut(pxPerSecond: number): number {
  const index = ZOOM_LEVELS.indexOf(pxPerSecond as (typeof ZOOM_LEVELS)[number]);
  return ZOOM_LEVELS[Math.max(index - 1, 0)];
}

export function timeToPx(seconds: number, pxPerSecond: number): number {
  return seconds * pxPerSecond;
}

export function pxToTime(px: number, pxPerSecond: number): number {
  return px / pxPerSecond;
}

/** Donde se dibuja un clip: su izquierda y su ancho en píxeles. */
export function clipRect(clip: Clip, pxPerSecond: number): { left: number; width: number } {
  return { left: timeToPx(clip.start, pxPerSecond), width: timeToPx(clipLength(clip), pxPerSecond) };
}

/** Los ids de los clips que se cruzan con el rango [from, to) de la línea de tiempo, en el orden del documento. */
export function selectInRange(clips: Clip[], from: number, to: number): string[] {
  return clips
    .filter((clip) => clip.start < to && clip.start + clipLength(clip) > from)
    .map((clip) => clip.id);
}

/** Mueve la selección como un bloque. Si choca, elige el desplazamiento libre más cercano. */
export function moveClips(doc: Doc, ids: string[], delta: number): Doc {
  const selectedIds = new Set(ids);
  const selected = doc.clips.filter((clip) => selectedIds.has(clip.id));
  if (selected.length === 0) return doc;

  const obstacles = doc.clips.filter((clip) => !selectedIds.has(clip.id));
  const edges = selected.flatMap((clip) => [
    -clip.start,
    ...obstacles
      .filter((other) => other.track === clip.track)
      .flatMap((other) => [other.start - clip.start - clipLength(clip), other.start + clipLength(other) - clip.start]),
  ]);
  const candidates = [0, delta, ...edges].filter((movement) =>
    selected.every((clip) => {
      const start = clip.start + movement;
      return (
        start >= 0 &&
        !obstacles.some(
          (other) => other.track === clip.track && overlaps(start, clipLength(clip), other),
        )
      );
    }),
  );
  const movement = candidates.reduce((best, candidate) => {
    const bestDistance = Math.abs(best - delta);
    const candidateDistance = Math.abs(candidate - delta);
    return candidateDistance < bestDistance || (candidateDistance === bestDistance && candidate < best)
      ? candidate
      : best;
  }, 0);

  const movedById = new Map<string, Clip>();
  for (const clip of selected) {
    const isolated = { ...doc, clips: [...obstacles, clip] };
    const moved = apply(isolated, {
      type: 'moveClip',
      id: clip.id,
      track: clip.track,
      start: clip.start + movement,
    });
    movedById.set(clip.id, moved.clips[obstacles.length] as Clip);
  }
  return { ...doc, clips: doc.clips.map((clip) => movedById.get(clip.id) ?? clip) };
}

/**
 * Los tiempos a los que se puede pegar un borde (D-8): el 0, el cabezal, los marcadores y los bordes de los clips
 * que no se mueven. `excludeIds` son los clips que se arrastran.
 */
export function snapCandidates(doc: Doc, excludeIds: string[], cursor: number): number[] {
  const edges = doc.clips
    .filter((clip) => !excludeIds.includes(clip.id))
    .flatMap((clip) => [clip.start, clip.start + clipLength(clip)]);
  return [0, cursor, ...doc.markers.map((marker) => marker.t), ...edges];
}

function overlaps(start: number, length: number, other: Clip): boolean {
  return start < other.start + clipLength(other) && other.start < start + length;
}
