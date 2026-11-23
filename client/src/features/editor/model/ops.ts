/**
 * Operaciones puras sobre el documento del editor. Espejo de `server/src/content_studio/editor/ops.py`:
 * las mismas fixtures (`server/tests/fixtures/editor/ops-*.json`) dan el mismo resultado en las dos.
 */

import { clipLength } from './validate';
import type { Clip, Doc, Op } from './types';

/** Una operación que no se puede aplicar, con su código del catálogo como mensaje. */
export class OpError extends Error {
  constructor(public readonly code: string) {
    super(code);
    this.name = 'OpError';
  }
}

/** Aplica `op` a una copia de `doc`. `op.type` nombra la operación. */
export function apply(doc: Doc, op: Op): Doc {
  const handler = HANDLERS[op.type as Op['type']];
  if (handler === undefined) throw new OpError('unknown_op');
  const result = structuredClone(doc);
  handler(result, op as never);
  return result;
}

/**
 * Mueve un clip a otra pista o a otro tiempo. En su pista no puede pisar a otro: queda pegado al hueco libre más
 * cercano (el borde de un clip vecino o el inicio). Superponer en otra pista sí está permitido.
 */
function moveClip(doc: Doc, op: Extract<Op, { type: 'moveClip' }>): void {
  const clip = findClip(doc, op.id);
  const others = doc.clips.filter((other) => other !== clip && other.track === op.track);
  if (others.length === 0) {
    Object.assign(clip, { track: op.track, start: Math.max(0, op.start) });
    return;
  }
  const length = clipLength(clip);
  const ends = others.map((other) => other.start + clipLength(other));
  const edges = [0, op.start, Math.max(...ends), ...ends, ...others.map((other) => other.start - length)];
  const free = edges.filter((t) => t >= 0 && !others.some((other) => overlaps(t, length, other)));
  // Igual que `min(key=(abs(t - requested), t))` del espejo en Python: gana el más cercano y, en empate, el menor.
  const best = free.reduce((a, b) => {
    const da = Math.abs(a - op.start);
    const db = Math.abs(b - op.start);
    return db < da || (db === da && b < a) ? b : a;
  });
  Object.assign(clip, { track: op.track, start: best });
}

/** Actualiza propiedades persistidas de una pista, como espejo del server. */
function setTrack(doc: Doc, op: Extract<Op, { type: 'setTrack' }>): void {
  const track = doc.tracks.find((candidate) => candidate.id === op.id);
  if (track === undefined) throw new OpError('unknown_track');
  Object.assign(track, op.changes);
}

/** Agrega una copia de un clip importado o grabado. */
function addClip(doc: Doc, op: Extract<Op, { type: 'addClip' }>): void {
  doc.clips.push(structuredClone(op.clip));
}

/** Actualiza los fundidos pedidos del clip. */
function setFade(doc: Doc, op: Extract<Op, { type: 'setFade' }>): void {
  const clip = findClip(doc, op.id);
  if (op.fade_in !== undefined) clip.fade_in = op.fade_in;
  if (op.fade_out !== undefined) clip.fade_out = op.fade_out;
}

/** Actualiza la ganancia del clip en dB. */
function setGain(doc: Doc, op: Extract<Op, { type: 'setGain' }>): void {
  findClip(doc, op.id).gain_db = op.gain_db;
}

/** Inserta una pista de audio en el índice indicado o al final. */
function addTrack(doc: Doc, op: Extract<Op, { type: 'addTrack' }>): void {
  if (doc.tracks.some((track) => track.id === op.track.id)) throw new OpError('duplicate_id');
  const index = Math.max(0, Math.min(op.index ?? doc.tracks.length, doc.tracks.length));
  doc.tracks.splice(index, 0, structuredClone(op.track));
}

/** Quita una pista y sus clips. */
function removeTrack(doc: Doc, op: Extract<Op, { type: 'removeTrack' }>): void {
  const exists = doc.tracks.some((track) => track.id === op.id);
  if (!exists) throw new OpError('unknown_track');
  doc.tracks = doc.tracks.filter((track) => track.id !== op.id);
  doc.clips = doc.clips.filter((clip) => clip.track !== op.id);
}

/** Mueve una pista al índice visual indicado, limitado al rango de pistas. */
function reorderTracks(doc: Doc, op: Extract<Op, { type: 'reorderTracks' }>): void {
  const index = doc.tracks.findIndex((track) => track.id === op.id);
  if (index < 0) throw new OpError('unknown_track');
  const [track] = doc.tracks.splice(index, 1);
  const destination = Math.max(0, Math.min(op.index, doc.tracks.length));
  doc.tracks.splice(destination, 0, track);
}

/** Agrega un marcador al proyecto. */
function addMarker(doc: Doc, op: Extract<Op, { type: 'addMarker' }>): void {
  doc.markers.push(structuredClone(op.marker));
}

/** Mueve un marcador a otro tiempo. */
function moveMarker(doc: Doc, op: Extract<Op, { type: 'moveMarker' }>): void {
  const marker = doc.markers.find((item) => item.id === op.id);
  if (marker === undefined) throw new OpError('unknown_marker');
  marker.t = op.t;
}

/** Renombra un marcador existente. */
function renameMarker(doc: Doc, op: Extract<Op, { type: 'renameMarker' }>): void {
  const marker = doc.markers.find((item) => item.id === op.id);
  if (marker === undefined) throw new OpError('unknown_marker');
  marker.label = op.label;
}

/** Quita el marcador con ese id, si todavía existe. */
function deleteMarker(doc: Doc, op: Extract<Op, { type: 'deleteMarker' }>): void {
  doc.markers = doc.markers.filter((marker) => marker.id !== op.id);
}

/** Reasigna todas las instancias de una fuente compartida. */
function replaceSource(doc: Doc, op: Extract<Op, { type: 'replaceSource' }>): void {
  for (const clip of doc.clips) if (clip.src === op.from) clip.src = op.to;
}

/** Recorta un borde del clip hasta el tiempo `t`: el inicio mueve `start` y `src_in`; el final cambia `src_out`. */
function trimClip(doc: Doc, op: Extract<Op, { type: 'trimClip' }>): void {
  const clip = findClip(doc, op.id);
  if (op.edge === 'start') {
    const delta = op.t - clip.start;
    if (clip.src_in + delta < 0) throw new OpError('bad_trim');
    Object.assign(clip, { start: op.t, src_in: clip.src_in + delta });
  } else {
    const length = op.t - clip.start;
    if (length <= 0) throw new OpError('bad_trim');
    clip.src_out = clip.src_in + length;
  }
}

/** Corta en `t` cada clip que lo cruza (o solo los de `ids`). La mitad derecha se llama `<id>-r`. */
function splitAt(doc: Doc, op: Extract<Op, { type: 'splitAt' }>): void {
  for (const clip of [...doc.clips]) {
    if (op.ids !== undefined && !op.ids.includes(clip.id)) continue;
    if (!(clip.start < op.t && op.t < clip.start + clipLength(clip))) continue;
    const left = op.t - clip.start;
    const right: Clip = { ...clip, id: `${clip.id}-r`, start: op.t, src_in: clip.src_in + left, fade_in: 0 };
    Object.assign(clip, { src_out: clip.src_in + left, fade_out: 0 });
    doc.clips.push(right);
  }
}

/** Borra los clips de `ids`. Con `ripple`, los clips que venían después en su pista se corren hacia atrás. */
function deleteClips(doc: Doc, op: Extract<Op, { type: 'deleteClips' }>): void {
  const gone = doc.clips.filter((clip) => op.ids.includes(clip.id));
  doc.clips = doc.clips.filter((clip) => !op.ids.includes(clip.id));
  if (!op.ripple) return;
  // De atrás hacia delante, como en el espejo de Python: cada borrado corre lo que va después de su final.
  for (const removed of [...gone].sort((a, b) => b.start - a.start)) {
    const end = removed.start + clipLength(removed);
    for (const clip of doc.clips) {
      if (clip.track === removed.track && clip.start >= end) clip.start -= clipLength(removed);
    }
  }
}

/** Une `b` detrás de `a` con un cruce de `d` segundos: `b` empieza `d` antes del final de `a`, con fundido. */
function crossfade(doc: Doc, op: Extract<Op, { type: 'crossfade' }>): void {
  const a = findClip(doc, op.a);
  const b = findClip(doc, op.b);
  Object.assign(b, { start: a.start + clipLength(a) - op.d, fade_in: op.d });
  a.fade_out = op.d;
}

function findClip(doc: Doc, id: string): Clip {
  const clip = doc.clips.find((candidate) => candidate.id === id);
  if (clip === undefined) throw new OpError('unknown_clip');
  return clip;
}

/** Si un clip que empieza en `start` y dura `length` se cruza con `other` en el tiempo. */
function overlaps(start: number, length: number, other: Clip): boolean {
  return start < other.start + clipLength(other) && other.start < start + length;
}

const HANDLERS: { [K in Op['type']]: (doc: Doc, op: Extract<Op, { type: K }>) => void } = {
  addClip,
  addTrack,
  addMarker,
  deleteMarker,
  moveMarker,
  removeTrack,
  reorderTracks,
  renameMarker,
  replaceSource,
  setFade,
  setGain,
  moveClip,
  setTrack,
  trimClip,
  splitAt,
  deleteClips,
  crossfade,
};
