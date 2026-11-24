import { clipLength } from '../model/validate';
import type { AudioClip, AudioTrack, Clip, Doc } from '../model/types';

export const PRELOAD_WINDOW_SEC = 2;
export const DRIFT_TOLERANCE_SEC = 0.04;

export type PlaybackClip = { clip: AudioClip; track: AudioTrack };

function isAudioClip(clip: Clip): clip is AudioClip {
  return 'gain_db' in clip && typeof clip.gain_db === 'number';
}

/** Clips que se oyen según mute y solo, en el mismo orden que el render del proyecto. */
export function audibleClips(doc: Doc): PlaybackClip[] {
  const tracks = new Map(doc.tracks.map((track) => [track.id, track]));
  const audioTracks = doc.tracks.filter((track): track is AudioTrack => track.kind === 'audio');
  const soloed = new Set(audioTracks.filter((track) => track.solo).map((track) => track.id));
  return doc.clips.flatMap((clip) => {
    const track = tracks.get(clip.track);
    return track?.kind === 'audio' && isAudioClip(clip) && !track.mute && (soloed.size === 0 || soloed.has(track.id))
      ? [{ clip, track }]
      : [];
  });
}

/** Clips audibles que cruzan la ventana de carga previa de dos segundos alrededor de `position`. */
export function activeClips(doc: Doc, position: number): PlaybackClip[] {
  return audibleClips(doc).filter(
    ({ clip }) => clip.start <= position + PRELOAD_WINDOW_SEC && clip.start + clipLength(clip) >= position - PRELOAD_WINDOW_SEC,
  );
}

/** Posición esperada dentro de la fuente de un clip mientras suena. */
export function sourceTimeAt(clip: AudioClip, position: number): number {
  return clip.src_in + Math.max(0, position - clip.start) * (clip.speed ?? 1);
}

/** Puntos de rampa lineal en segundos de timeline y ganancia lineal, tras sumar volumen de clip y pista. */
export function gainRamps(clip: AudioClip, track: Pick<AudioTrack, 'volume_db'>): [number, number][] {
  const peak = 10 ** ((clip.gain_db + track.volume_db) / 20);
  const end = clip.start + clipLength(clip);
  const points: [number, number][] = [];
  if (clip.fade_in > 0) points.push([clip.start, 0], [clip.start + clip.fade_in, peak]);
  if (clip.fade_out > 0) points.push([end - clip.fade_out, peak], [end, 0]);
  return points;
}

/** Ganancia instantánea del clip, incluida su envolvente y el volumen de pista. */
export function gainAt(clip: AudioClip, track: Pick<AudioTrack, 'volume_db'>, position: number): number {
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
  return Math.abs(expected - actual) > tolerance + Number.EPSILON * Math.max(1, Math.abs(expected), Math.abs(actual));
}
