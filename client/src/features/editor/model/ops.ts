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
  const group = linked(doc, clip);
  const destinations = group.map((member) => [member, member === clip ? op.track : member.track] as const);
  const others = doc.clips.filter(
    (other) => !group.includes(other) && destinations.some(([, track]) => other.track === track),
  );
  const edges = [0, op.start];
  for (const [member, track] of destinations) {
    for (const other of doc.clips) {
      if (group.includes(other) || other.track !== track) continue;
      edges.push(other.start + clipLength(other), other.start - clipLength(member));
    }
  }
  const free = edges.filter(
    (time) =>
      time >= 0 &&
      destinations.every(([member, track]) =>
        doc.clips
          .filter((other) => !group.includes(other) && other.track === track)
          .every((other) => !overlaps(time, clipLength(member), other)),
      ),
  );
  const end = Math.max(0, ...others.map((other) => other.start + clipLength(other)));
  if (free.length === 0) free.push(end);
  // Igual que `min(key=(abs(t - requested), t))` del espejo en Python: gana el más cercano y, en empate, el menor.
  const best = free.reduce((a, b) => {
    const da = Math.abs(a - op.start);
    const db = Math.abs(b - op.start);
    return db < da || (db === da && b < a) ? b : a;
  });
  const delta = best - clip.start;
  for (const [member, track] of destinations) Object.assign(member, { track, start: member.start + delta });
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
  const removed = doc.clips.filter((clip) => clip.track === op.id);
  const links = new Set(removed.map((clip) => clip.link).filter((link): link is string => link !== undefined));
  const removedIds = new Set(removed.map((clip) => clip.id));
  doc.tracks = doc.tracks.filter((track) => track.id !== op.id);
  doc.clips = doc.clips.filter((clip) => clip.track !== op.id);
  for (const clip of doc.clips) if (clip.link !== undefined && links.has(clip.link)) delete clip.link;
  doc.transitions = (doc.transitions ?? []).filter(
    (transition) => !removedIds.has(transition.a) && !removedIds.has(transition.b),
  );
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
  const group = linked(doc, clip);
  if (op.edge === 'start') {
    const delta = op.t - clip.start;
    if (group.some((member) => member.src_in + delta * (member.speed ?? 1) < 0)) throw new OpError('bad_trim');
    for (const member of group) {
      Object.assign(member, { start: member.start + delta, src_in: member.src_in + delta * (member.speed ?? 1) });
    }
  } else {
    const length = op.t - clip.start;
    if (length <= 0) throw new OpError('bad_trim');
    for (const member of group) member.src_out = member.src_in + length * (member.speed ?? 1);
  }
}

/** Corta en `t` cada clip que lo cruza (o solo los de `ids`). La mitad derecha se llama `<id>-r`. */
function splitAt(doc: Doc, op: Extract<Op, { type: 'splitAt' }>): void {
  const ids = op.ids === undefined ? undefined : new Set(op.ids);
  if (ids !== undefined) {
    for (const clip of doc.clips) {
      if (ids.has(clip.id) && clip.link !== undefined) {
        for (const member of doc.clips) if (member.link === clip.link) ids.add(member.id);
      }
    }
  }
  for (const clip of [...doc.clips]) {
    if (ids !== undefined && !ids.has(clip.id)) continue;
    if (!(clip.start < op.t && op.t < clip.start + clipLength(clip))) continue;
    const left = op.t - clip.start;
    const sourceLeft = left * (clip.speed ?? 1);
    const right: Clip = { ...clip, id: `${clip.id}-r`, start: op.t, src_in: clip.src_in + sourceLeft, fade_in: 0 };
    Object.assign(clip, { src_out: clip.src_in + sourceLeft, fade_out: 0 });
    doc.clips.push(right);
  }
}

/** Borra los clips de `ids`. Con `ripple`, los clips que venían después en su pista se corren hacia atrás. */
function deleteClips(doc: Doc, op: Extract<Op, { type: 'deleteClips' }>): void {
  const ids = new Set(op.ids);
  for (const clip of doc.clips) {
    if (ids.has(clip.id) && clip.link !== undefined) {
      for (const member of doc.clips) if (member.link === clip.link) ids.add(member.id);
    }
  }
  const gone = doc.clips.filter((clip) => ids.has(clip.id));
  doc.clips = doc.clips.filter((clip) => !ids.has(clip.id));
  doc.transitions = (doc.transitions ?? []).filter(
    (transition) => !ids.has(transition.a) && !ids.has(transition.b),
  );
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

/** Enlaza clips y limpia los grupos previos a los que pertenecían. */
function linkClips(doc: Doc, op: Extract<Op, { type: 'linkClips' }>): void {
  const ids = [...new Set(op.ids)];
  if (ids.length < 2 || !op.link) throw new OpError('bad_link');
  const selected = ids.map((id) => findClip(doc, id));
  const oldLinks = new Set(selected.map((clip) => clip.link).filter((link): link is string => link !== undefined));
  for (const clip of doc.clips) if (clip.link !== undefined && oldLinks.has(clip.link)) delete clip.link;
  for (const clip of selected) clip.link = op.link;
}

/** Desenlaza por completo los grupos seleccionados. */
function unlinkClips(doc: Doc, op: Extract<Op, { type: 'unlinkClips' }>): void {
  const selected = op.ids.map((id) => findClip(doc, id));
  const links = new Set(selected.map((clip) => clip.link).filter((link): link is string => link !== undefined));
  for (const clip of doc.clips) if (clip.link !== undefined && links.has(clip.link)) delete clip.link;
}

function linked(doc: Doc, clip: Clip): Clip[] {
  return clip.link === undefined ? [clip] : doc.clips.filter((member) => member.link === clip.link);
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
  linkClips,
  unlinkClips,
};
