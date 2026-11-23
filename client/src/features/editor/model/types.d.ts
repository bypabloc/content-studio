/** Modelo del proyecto del editor, esquema v1. Espejo de `server/src/content_studio/editor/project.py`. */

export interface Track {
  id: string;
  kind: 'audio';
  name: string;
  volume_db: number;
  mute: boolean;
  solo: boolean;
  locked: boolean;
  height: number;
}

/** Un clip usa el rango `src_in`–`src_out` de su fuente y se coloca en `start` de la línea de tiempo. */
export interface Clip {
  id: string;
  track: string;
  src: string;
  src_in: number;
  src_out: number;
  start: number;
  gain_db: number;
  fade_in: number;
  fade_out: number;
}

export interface Marker {
  id: string;
  t: number;
  label: string;
  color: string;
}

export interface Doc {
  version: 1;
  name: string;
  sample_rate: 48000;
  tracks: Track[];
  clips: Clip[];
  markers: Marker[];
}

export interface ValidationError {
  code: string;
  id: string;
}

/** Las operaciones de `ops.py`. Cada una nombra su tipo en `type`. */
export type Op =
  | { type: 'addClip'; clip: Clip }
  | { type: 'addTrack'; track: Track; index?: number }
  | { type: 'removeTrack'; id: string }
  | { type: 'reorderTracks'; id: string; index: number }
  | { type: 'replaceSource'; from: string; to: string }
  | { type: 'setFade'; id: string; fade_in?: number; fade_out?: number }
  | { type: 'setGain'; id: string; gain_db: number }
  | { type: 'addMarker'; marker: Marker }
  | { type: 'moveMarker'; id: string; t: number }
  | { type: 'renameMarker'; id: string; label: string }
  | { type: 'deleteMarker'; id: string }
  | { type: 'moveClip'; id: string; track: string; start: number }
  | { type: 'setTrack'; id: string; changes: Partial<Pick<Track, 'volume_db' | 'mute' | 'solo' | 'locked'>> }
  | { type: 'trimClip'; id: string; edge: 'start' | 'end'; t: number }
  | { type: 'splitAt'; t: number; ids?: string[] }
  | { type: 'deleteClips'; ids: string[]; ripple?: boolean }
  | { type: 'crossfade'; a: string; b: string; d: number };
