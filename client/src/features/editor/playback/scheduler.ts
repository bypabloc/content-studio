import { clipLength } from '../model/validate';
import type { Clip, Doc, Track } from '../model/types';

export const DRIFT_TOLERANCE_SEC = 0.05;

export type PlaybackClip = { clip: Clip; track: Track };

/** Clips que se oyen según mute y solo, en el mismo orden que el render del proyecto. */
export function audibleClips(doc: Doc): PlaybackClip[] {
  const tracks = new Map(doc.tracks.map((track) => [track.id, track]));
  const soloed = new Set(doc.tracks.filter((track) => track.solo).map((track) => track.id));
  return doc.clips.flatMap((clip) => {
    const track = tracks.get(clip.track);
    return track && !track.mute && (soloed.size === 0 || soloed.has(track.id)) ? [{ clip, track }] : [];
  });
}

/** Clips audibles cuyo intervalo de timeline incluye `position`. */
export function activeClips(doc: Doc, position: number): PlaybackClip[] {
  return audibleClips(doc).filter(({ clip }) => clip.start <= position && position < clip.start + clipLength(clip));
}

/** Posición esperada dentro de la fuente de un clip mientras suena. */
export function sourceTimeAt(clip: Clip, position: number): number {
  return clip.src_in + Math.max(0, position - clip.start);
}

/** Puntos de rampa lineal en segundos de timeline y ganancia lineal, tras sumar volumen de clip y pista. */
export function gainRamps(clip: Clip, track: Pick<Track, 'volume_db'>): [number, number][] {
  const peak = 10 ** ((clip.gain_db + track.volume_db) / 20);
  const end = clip.start + clipLength(clip);
  const points: [number, number][] = [];
  if (clip.fade_in > 0) points.push([clip.start, 0], [clip.start + clip.fade_in, peak]);
  if (clip.fade_out > 0) points.push([end - clip.fade_out, peak], [end, 0]);
  return points;
}

/** Ganancia instantánea del clip, incluida su envolvente y el volumen de pista. */
export function gainAt(clip: Clip, track: Pick<Track, 'volume_db'>, position: number): number {
  const end = clip.start + clipLength(clip);
  if (position < clip.start || position >= end) return 0;
  let envelope = 1;
  if (clip.fade_in > 0) envelope = Math.min(envelope, (position - clip.start) / clip.fade_in);
  if (clip.fade_out > 0) envelope = Math.min(envelope, (end - position) / clip.fade_out);
  return (10 ** ((clip.gain_db + track.volume_db) / 20)) * Math.max(0, Math.min(1, envelope));
}

/** Posición estable desde el reloj de audio; limita el resultado al final del proyecto. */
export function positionAt(startPosition: number, startedAt: number, now: number, total: number): number {
  return Math.min(total, Math.max(0, startPosition + Math.max(0, now - startedAt)));
}

/** Determina si conviene buscar el elemento al tiempo esperado para corregir su deriva. */
export function shouldCorrectDrift(expected: number, actual: number, tolerance = DRIFT_TOLERANCE_SEC): boolean {
  return Math.abs(expected - actual) > tolerance;
}
