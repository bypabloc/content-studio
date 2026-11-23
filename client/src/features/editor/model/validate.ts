/** Validación y duración del proyecto. Espejo de `validate` y `duration` en `server/src/content_studio/editor/project.py`. */

import type { Clip, Doc, ValidationError } from './types';

/** La duración del clip en la línea de tiempo: el rango de su fuente. */
export function clipLength(clip: Clip): number {
  return clip.src_out - clip.src_in;
}

/** El final del clip que más tarde termina; 0 sin clips. */
export function duration(doc: Doc): number {
  if (doc.clips.length === 0) return 0;
  return Math.max(...doc.clips.map((clip) => clip.start + clipLength(clip)));
}

/**
 * Los errores del documento: código del catálogo e id del clip. Lista vacía si es válido.
 * Un id repetido se reporta una vez. Los dos fades no pueden sumar más que la duración del clip.
 */
export function validate(doc: Doc): ValidationError[] {
  const errors: ValidationError[] = [];
  const tracks = new Set(doc.tracks.map((track) => track.id));
  const seen = new Set<string>();
  const reported = new Set<string>();
  for (const clip of doc.clips) {
    if (seen.has(clip.id) && !reported.has(clip.id)) {
      errors.push({ code: 'duplicate_id', id: clip.id });
      reported.add(clip.id);
    }
    seen.add(clip.id);
    errors.push(...clipErrors(clip, tracks));
  }
  return errors;
}

/** Los errores de un clip que no dependen de los demás. */
function clipErrors(clip: Clip, tracks: Set<string>): ValidationError[] {
  const found: ValidationError[] = [];
  if (!tracks.has(clip.track)) found.push({ code: 'unknown_track', id: clip.id });
  if (clip.start < 0) found.push({ code: 'negative_start', id: clip.id });
  if (clip.src_in < 0 || clip.src_out <= clip.src_in) found.push({ code: 'bad_source_range', id: clip.id });
  if (clip.fade_in + clip.fade_out > clipLength(clip)) found.push({ code: 'fade_too_long', id: clip.id });
  return found;
}
