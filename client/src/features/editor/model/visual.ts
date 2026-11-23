import { clipLength } from './validate';
import { valueAt } from './keyframes';
import type { Doc, Keyframe, TransitionType, VisualClip } from './types';

export type VisualProperty =
  | 'x'
  | 'y'
  | 'scale_x'
  | 'scale_y'
  | 'rotation'
  | 'opacity'
  | 'anchor_x'
  | 'anchor_y'
  | 'crop_l'
  | 'crop_t'
  | 'crop_r'
  | 'crop_b';

const KEYFRAME_EPSILON = 1e-6;

/** Cambia un valor del clip; si está animado, escribe un keyframe en el tiempo indicado. */
export function writeVisualValue(doc: Doc, clipId: string, property: VisualProperty, time: number, value: number): Doc {
  const next = structuredClone(doc);
  const clip = findVisualClip(next, clipId);
  const keyframes = clip.keyframes[property] ?? [];
  const relativeTime = frameTime(next, clip, time);
  if (keyframes.length > 0) {
    clip.keyframes[property] = upsert(keyframes, relativeTime, value);
  } else {
    setBaseValue(clip, property, value);
  }
  return next;
}

/** Activa un keyframe con el valor interpolado o quita el que coincide con el cabezal. */
export function toggleKeyframe(doc: Doc, clipId: string, property: VisualProperty, time: number): Doc {
  const next = structuredClone(doc);
  const clip = findVisualClip(next, clipId);
  const frames = clip.keyframes[property] ?? [];
  const relativeTime = frameTime(next, clip, time);
  const index = frames.findIndex((frame) => Math.abs(frame.t - relativeTime) <= KEYFRAME_EPSILON);
  if (index >= 0) {
    frames.splice(index, 1);
    if (frames.length === 0) delete clip.keyframes[property];
    else clip.keyframes[property] = frames;
    return next;
  }
  clip.keyframes[property] = upsert(frames, relativeTime, valueAt(frames, relativeTime, baseValue(clip, property)));
  return next;
}

/** Arrastra un keyframe, lo limita al clip y mantiene al menos un cuadro entre puntos vecinos. */
export function moveKeyframe(
  doc: Doc,
  clipId: string,
  property: VisualProperty,
  fromTime: number,
  toTime: number,
): Doc {
  const next = structuredClone(doc);
  const clip = findVisualClip(next, clipId);
  const frames = clip.keyframes[property] ?? [];
  const index = frames.findIndex((frame) => Math.abs(frame.t - fromTime) <= KEYFRAME_EPSILON);
  if (index < 0) return next;

  const [moving] = frames.splice(index, 1);
  const fps = next.canvas.fps;
  const maxFrame = Math.floor(clipLength(clip) * fps + KEYFRAME_EPSILON);
  const targetFrame = Math.max(0, Math.min(maxFrame, Math.round(toTime * fps)));
  const direction = Math.sign(targetFrame / fps - moving.t) || 1;
  const occupied = (candidate: number) => frames.some((item) => Math.abs(item.t - candidate / fps) < 1 / fps - KEYFRAME_EPSILON);
  let destination = -1;
  for (let offset = 0; offset <= frames.length + 1 && destination < 0; offset += 1) {
    const candidates = offset === 0 ? [targetFrame] : [targetFrame + direction * offset, targetFrame - direction * offset];
    destination = candidates.find((candidate) => candidate >= 0 && candidate <= maxFrame && !occupied(candidate)) ?? -1;
  }
  if (destination < 0) {
    frames.push(moving);
    clip.keyframes[property] = frames.sort((a, b) => a.t - b.t);
    return next;
  }
  const updated = { ...moving, t: destination / fps };
  clip.keyframes[property] = [...frames, updated].sort((a, b) => a.t - b.t);
  return next;
}

/** Cambia la curva del keyframe más cercano al cabezal si está dentro de medio cuadro. */
export function setKeyframeEase(
  doc: Doc,
  clipId: string,
  property: VisualProperty,
  time: number,
  ease: Keyframe['ease'],
): Doc {
  const next = structuredClone(doc);
  const clip = findVisualClip(next, clipId);
  const relativeTime = frameTime(next, clip, time);
  const tolerance = 0.5 / next.canvas.fps;
  const frames = clip.keyframes[property] ?? [];
  const index = frames.findIndex((frame) => Math.abs(frame.t - relativeTime) <= tolerance);
  if (index >= 0) clip.keyframes[property][index] = { ...frames[index], ease };
  return next;
}

/** Crea un fundido en el corte más cercano y desplaza el segundo clip para formar el solapamiento. */
export function addTransitionAtCut(
  doc: Doc,
  trackId: string,
  time: number,
  type: TransitionType,
  id: string,
  duration = 0.5,
): Doc | null {
  const track = doc.tracks.find((item) => item.id === trackId && item.kind === 'video');
  if (!track || duration <= 0 || doc.transitions.some((transition) => transition.id === id)) return null;
  const clips = doc.clips
    .filter((clip): clip is VisualClip => 'media' in clip && clip.track === trackId)
    .sort((a, b) => a.start - b.start);
  const tolerance = 0.5 / doc.canvas.fps;
  const pair = clips.slice(0, -1).map((a, index) => ({ a, b: clips[index + 1] })).find(({ a, b }) => {
    const cut = a.start + clipLength(a);
    return Math.abs(cut - b.start) <= tolerance && Math.abs(cut - time) <= tolerance;
  });
  if (!pair || doc.transitions.some((transition) => transition.a === pair.a.id && transition.b === pair.b.id)) return null;

  const oneFrame = 1 / doc.canvas.fps;
  const requested = Math.max(oneFrame, Math.round(duration / oneFrame) * oneFrame);
  const transitionDuration = Math.min(requested, clipLength(pair.a), clipLength(pair.b));
  if (transitionDuration <= 0) return null;
  const next = structuredClone(doc);
  const nextClip = next.clips.find((clip) => clip.id === pair.b.id);
  if (!nextClip) return null;
  nextClip.start = pair.a.start + clipLength(pair.a) - transitionDuration;
  next.transitions.push({
    id,
    track: trackId,
    a: pair.a.id,
    b: pair.b.id,
    type,
    duration: transitionDuration,
  });
  return next;
}

/** Ajusta la duración de una transición y vuelve a alinear el segundo clip con el final del primero. */
export function resizeTransition(doc: Doc, transitionId: string, requested: number): Doc | null {
  const transition = doc.transitions.find((item) => item.id === transitionId);
  if (!transition || !Number.isFinite(requested)) return null;
  const a = doc.clips.find((clip) => clip.id === transition.a);
  const b = doc.clips.find((clip) => clip.id === transition.b);
  if (!a || !b || !('media' in a) || !('media' in b)) return null;
  const frame = 1 / doc.canvas.fps;
  const duration = Math.min(Math.max(frame, Math.round(requested / frame) * frame), clipLength(a), clipLength(b));
  const next = structuredClone(doc);
  const updated = next.transitions.find((item) => item.id === transitionId);
  const nextB = next.clips.find((clip) => clip.id === b.id);
  if (!updated || !nextB) return null;
  updated.duration = duration;
  nextB.start = a.start + clipLength(a) - duration;
  return next;
}

function findVisualClip(doc: Doc, id: string): VisualClip {
  const clip = doc.clips.find((item) => item.id === id);
  if (clip === undefined || (clip.media !== 'image' && clip.media !== 'video')) {
    throw new Error(`unknown visual clip: ${id}`);
  }
  return clip;
}

function frameTime(doc: Doc, clip: VisualClip, globalTime: number): number {
  const length = clipLength(clip);
  const relative = Math.max(0, Math.min(length, globalTime - clip.start));
  return Math.max(0, Math.min(length, Math.round(relative * doc.canvas.fps) / doc.canvas.fps));
}

function upsert(frames: Keyframe[], time: number, value: number): Keyframe[] {
  const existing = frames.find((frame) => Math.abs(frame.t - time) <= KEYFRAME_EPSILON);
  const updated = existing
    ? frames.map((frame) => (frame === existing ? { ...frame, value } : frame))
    : [...frames, { t: time, value, ease: 'linear' as const }];
  return updated.sort((a, b) => a.t - b.t);
}

function baseValue(clip: VisualClip, property: VisualProperty): number {
  const edge = cropEdge(property);
  return edge ? clip.transform.crop[edge] : clip.transform[property as keyof Omit<VisualClip['transform'], 'crop'>];
}

function setBaseValue(clip: VisualClip, property: VisualProperty, value: number): void {
  const edge = cropEdge(property);
  if (edge) {
    clip.transform.crop[edge] = value;
  } else {
    clip.transform[property as keyof Omit<VisualClip['transform'], 'crop'>] = value;
  }
}

function cropEdge(property: VisualProperty): 'l' | 't' | 'r' | 'b' | undefined {
  if (property === 'crop_l') return 'l';
  if (property === 'crop_t') return 't';
  if (property === 'crop_r') return 'r';
  if (property === 'crop_b') return 'b';
  return undefined;
}
