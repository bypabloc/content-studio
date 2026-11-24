/** Validación y duración del proyecto. Espejo de project.py. */

import type { Clip, Doc, Track, ValidationError, VisualClip } from './types';
import { clipDuration } from './timing';

const EASES = new Set(['linear', 'ease-in-out', 'hold']);
// cspell:ignore fadeblack fadewhite wipeleft wiperight slideleft slideright circleopen: tipos de transición de FFmpeg
const TRANSITIONS = new Set(['fade', 'fadeblack', 'fadewhite', 'wipeleft', 'wiperight', 'slideleft', 'slideright', 'circleopen']);
const KEYFRAME_KEYS = new Set([
  'x', 'y', 'scale_x', 'scale_y', 'rotation', 'opacity', 'anchor_x', 'anchor_y', 'crop_l', 'crop_t', 'crop_r', 'crop_b',
]);

/** La duración del clip en la línea de tiempo: el rango de su fuente. */
export function clipLength(clip: Clip): number {
  try {
    return clipDuration(clip);
  } catch {
    return clip.src_out - clip.src_in;
  }
}

/** El final del clip que más tarde termina; 0 sin clips. */
export function duration(doc: Doc): number {
  if (doc.clips.length === 0) return 0;
  return Math.max(...doc.clips.map((clip) => clip.start + clipLength(clip)));
}

/** Los errores del documento: código del catálogo e id de la entidad. Lista vacía si es válido. */
export function validate(doc: Doc): ValidationError[] {
  const errors: ValidationError[] = [];
  const tracks = new Map(doc.tracks.map((track) => [track.id, track]));
  const clips = new Map(doc.clips.map((clip) => [clip.id, clip]));
  const seen = new Set<string>();
  const reported = new Set<string>();
  for (const clip of doc.clips) {
    if (seen.has(clip.id) && !reported.has(clip.id)) {
      errors.push({ code: 'duplicate_id', id: clip.id });
      reported.add(clip.id);
    }
    seen.add(clip.id);
    errors.push(...clipErrors(clip, tracks, doc.version));
  }
  if (doc.version === 2 || doc.version === 3) {
    if (doc.version === 3) errors.push(...doc.tracks.flatMap(trackErrors));
    errors.push(...transitionErrors(doc.transitions ?? [], clips, tracks));
    errors.push(...linkErrors(doc.clips, tracks));
  }
  return errors;
}

/** Los errores de un clip, incluidos el tipo de pista y sus datos visuales. */
function clipErrors(clip: Clip, tracks: Map<string, Track>, version: Doc['version']): ValidationError[] {
  const found: ValidationError[] = [];
  const track = tracks.get(clip.track);
  if (track === undefined) found.push({ code: 'unknown_track', id: clip.id });
  else if (version === 3 ? track.kind === 'subtitles' || (track.kind === 'video') !== ('media' in clip) : (track.kind === 'video') !== ('media' in clip)) {
    found.push({ code: 'wrong_track_kind', id: clip.id });
  }
  if (clip.start < 0) found.push({ code: 'negative_start', id: clip.id });
  if (clip.src_in < 0 || clip.src_out <= clip.src_in) found.push({ code: 'bad_source_range', id: clip.id });
  if (clip.fade_in + clip.fade_out > clipLength(clip)) found.push({ code: 'fade_too_long', id: clip.id });
  if (version === 3 && (!Number.isFinite(clip.speed) || clip.speed === undefined || clip.speed < 0.25 || clip.speed > 4)) {
    found.push({ code: 'bad_speed', id: clip.id });
  }
  if ('media' in clip) found.push(...visualErrors(clip as VisualClip, version));
  return found;
}

/** Valida formato, transformación y keyframes de un clip visual. */
function visualErrors(clip: VisualClip, version: Doc['version']): ValidationError[] {
  const found: ValidationError[] = [];
  const transform = clip.transform as unknown as Record<string, unknown>;
  const crop = transform?.crop as Record<string, unknown> | undefined;
  const fields = ['x', 'y', 'scale_x', 'scale_y', 'rotation', 'opacity', 'anchor_x', 'anchor_y'];
  let validTransform =
    (clip.media === 'video' || clip.media === 'image' || clip.media === 'text') &&
    transform !== undefined &&
    fields.every((field) => finiteNumber(transform[field])) &&
    crop !== undefined &&
    ['l', 't', 'r', 'b'].every((edge) => finiteNumber(crop[edge]));
  if (validTransform && crop) {
    validTransform =
      (transform.scale_x as number) > 0 &&
      (transform.scale_y as number) > 0 &&
      between(transform.opacity, 0, 1) &&
      between(transform.anchor_x, 0, 1) &&
      between(transform.anchor_y, 0, 1) &&
      between(crop.l, 0, 1) && between(crop.t, 0, 1) && between(crop.r, 0, 1) && between(crop.b, 0, 1) &&
      (crop.l as number) + (crop.r as number) < 1 &&
      (crop.t as number) + (crop.b as number) < 1;
  }
  if (!validTransform) found.push({ code: 'bad_transform', id: clip.id });
  if (!validKeyframes(clip.keyframes, clipLength(clip))) found.push({ code: 'bad_keyframes', id: clip.id });
  if (version === 3) {
    if (!validColor(clip.color)) found.push({ code: 'bad_color', id: clip.id });
    if (!clip.blend_mode || !BLEND_MODES.has(clip.blend_mode)) found.push({ code: 'bad_blend_mode', id: clip.id });
    if (clip.chroma !== undefined && !validChroma(clip.chroma)) found.push({ code: 'bad_chroma', id: clip.id });
    if (clip.media === 'text' && !validText(clip.text, clip.raster)) found.push({ code: 'bad_text', id: clip.id });
  }
  return found;
}

function validKeyframes(keyframes: unknown, length: number): boolean {
  if (typeof keyframes !== 'object' || keyframes === null || Array.isArray(keyframes)) return false;
  for (const [property, frames] of Object.entries(keyframes)) {
    if (!KEYFRAME_KEYS.has(property) || !Array.isArray(frames)) return false;
    let previous = -1;
    for (const raw of frames) {
      if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) return false;
      const frame = raw as Record<string, unknown>;
      if (!finiteNumber(frame.t) || !finiteNumber(frame.value) || !between(frame.t, 0, length)) return false;
      if ((frame.t as number) <= previous || typeof frame.ease !== 'string' || !EASES.has(frame.ease)) return false;
      previous = frame.t as number;
    }
  }
  return true;
}

function transitionErrors(transitions: Doc['transitions'], clips: Map<string, Clip>, tracks: Map<string, Track>): ValidationError[] {
  return transitions.flatMap((transition) => {
    const a = clips.get(transition.a);
    const b = clips.get(transition.b);
    const track = tracks.get(transition.track);
    let valid = a !== undefined && b !== undefined && track?.kind === 'video';
    if (valid && a && b) {
      const overlap = a.start + clipLength(a) - b.start;
      valid =
        a.track === b.track && a.track === transition.track && 'media' in a && 'media' in b &&
        TRANSITIONS.has(transition.type) && finiteNumber(transition.duration) &&
        transition.duration > 0 && transition.duration <= Math.min(clipLength(a), clipLength(b)) &&
        Math.abs(overlap - transition.duration) <= 1e-9;
    }
    return valid ? [] : [{ code: 'bad_transition', id: transition.id }];
  });
}

function linkErrors(clips: Clip[], tracks: Map<string, Track>): ValidationError[] {
  const groups = new Map<string, Clip[]>();
  for (const clip of clips) {
    if (!clip.link) continue;
    groups.set(clip.link, [...(groups.get(clip.link) ?? []), clip]);
  }
  const found: ValidationError[] = [];
  for (const [link, group] of groups) {
    const audio = group.filter((clip) => tracks.get(clip.track)?.kind === 'audio' && !('media' in clip));
    const video = group.filter((clip) => 'media' in clip && clip.media === 'video');
    const audioClip = audio[0];
    const videoClip = video[0];
    const valid =
      group.length === 2 && audioClip !== undefined && videoClip !== undefined &&
      Math.abs(audioClip.start - videoClip.start) <= 1e-9 &&
      Math.abs(clipLength(audioClip) - clipLength(videoClip)) <= 1e-9;
    if (!valid) found.push({ code: 'bad_link', id: link });
  }
  return found;
}

function finiteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function between(value: unknown, min: number, max: number): boolean {
  return finiteNumber(value) && value >= min && value <= max;
}

const BLEND_MODES = new Set(['normal', 'multiply', 'screen', 'overlay', 'darken', 'lighten', 'add', 'difference']);

function trackErrors(track: Track): ValidationError[] {
  if (!new Set(['audio', 'video', 'subtitles']).has(track.kind)) return [{ code: 'bad_track_kind', id: track.id }];
  if (track.kind !== 'subtitles') return [];
  return track.subtitles_project ? [] : [{ code: 'bad_subtitles_track', id: track.id }];
}

function validColor(value: unknown): boolean {
  if (!isRecord(value)) return false;
  return (
    between(value.brightness, -1, 1) && between(value.contrast, 0, 2) &&
    between(value.saturation, 0, 3) && between(value.gamma, 0.1, 10) &&
    (value.lut === undefined || typeof value.lut === 'string')
  );
}

function validChroma(value: unknown): boolean {
  if (!isRecord(value)) return false;
  return (
    typeof value.color === 'string' && /^#[0-9a-f]{6}$/i.test(value.color) &&
    between(value.similarity, 0, 1) && between(value.blend, 0, 1) &&
    (value.despill === undefined || typeof value.despill === 'boolean')
  );
}

function validText(value: unknown, raster: string): boolean {
  if (!isRecord(value) || !raster.startsWith('media/text-') || raster.includes('..')) return false;
  if (!['content', 'font', 'color'].every((key) => typeof value[key] === 'string')) return false;
  if (!['weight', 'size', 'line_height', 'max_width'].every((key) => finiteNumber(value[key]) && value[key] > 0)) {
    return false;
  }
  if (!['left', 'center', 'right'].includes(String(value.align))) return false;
  const stroke = value.stroke;
  const shadow = value.shadow;
  const box = value.box;
  if (!isRecord(stroke) || !finiteNumber(stroke.width) || stroke.width < 0 || typeof stroke.color !== 'string') return false;
  if (!isRecord(shadow) || !['x', 'y', 'blur'].every((key) => finiteNumber(shadow[key]))) return false;
  if ((shadow.blur as number) < 0 || typeof shadow.color !== 'string') return false;
  return box === undefined || (
    isRecord(box) && typeof box.color === 'string' && finiteNumber(box.padding) && box.padding >= 0 &&
    finiteNumber(box.radius) && box.radius >= 0
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
