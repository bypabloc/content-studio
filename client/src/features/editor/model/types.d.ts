/** Modelo v2 del proyecto del editor. Espejo de server/src/content_studio/editor/project.py. */

export interface AudioTrack {
  id: string;
  kind: 'audio';
  name: string;
  volume_db: number;
  mute: boolean;
  solo: boolean;
  locked: boolean;
  height: number;
}

export interface VideoTrack {
  id: string;
  kind: 'video';
  name: string;
  opacity: number;
  hidden: boolean;
  locked: boolean;
  height?: number;
}

export interface SubtitleTrack {
  id: string;
  kind: 'subtitles';
  name: string;
  subtitles_project: string;
  locked: boolean;
  height?: number;
}

export type Track = AudioTrack | VideoTrack | SubtitleTrack;

export interface Canvas {
  width: number;
  height: number;
  fps: number;
  background: string;
}

export interface Transform {
  x: number;
  y: number;
  scale_x: number;
  scale_y: number;
  rotation: number;
  opacity: number;
  crop: { l: number; t: number; r: number; b: number };
  anchor_x: number;
  anchor_y: number;
}

export interface Keyframe {
  t: number;
  value: number;
  ease: 'linear' | 'ease-in-out' | 'hold';
}

export interface ColorEffects {
  brightness: number;
  contrast: number;
  saturation: number;
  gamma: number;
  lut?: string;
}

export interface ChromaKey {
  color: string;
  similarity: number;
  blend: number;
}

export type BlendMode = 'normal' | 'multiply' | 'screen' | 'overlay' | 'darken' | 'lighten' | 'add' | 'difference';

export interface TextStyle {
  content: string;
  font: string;
  weight: number;
  size: number;
  color: string;
  stroke: { width: number; color: string };
  shadow: { x: number; y: number; blur: number; color: string };
  box?: { color: string; padding: number; radius: number };
  align: 'left' | 'center' | 'right';
  line_height: number;
  max_width: number;
}

interface ClipBase {
  id: string;
  track: string;
  src: string;
  src_in: number;
  src_out: number;
  start: number;
  fade_in: number;
  fade_out: number;
  speed?: number;
  link?: string;
}

export interface AudioClip extends ClipBase {
  gain_db: number;
  media?: never;
  transform?: never;
  keyframes?: never;
}

interface VisualClipBase extends ClipBase {
  transform: Transform;
  keyframes: Record<string, Keyframe[]>;
  color?: ColorEffects;
  chroma?: ChromaKey;
  blend_mode?: BlendMode;
  gain_db?: never;
}

export interface VideoClip extends VisualClipBase {
  media: 'video';
}

export interface ImageClip extends VisualClipBase {
  media: 'image';
}

export interface TextClip extends VisualClipBase {
  media: 'text';
  raster: string;
  text: TextStyle;
}

export type VisualClip = VideoClip | ImageClip | TextClip;

export type Clip = AudioClip | VideoClip | ImageClip | TextClip;

export interface Marker {
  id: string;
  t: number;
  label: string;
  color: string;
}

export type TransitionType = 'fade' | 'fadeblack' | 'fadewhite' | 'wipeleft' | 'wiperight' | 'slideleft' | 'slideright' | 'circleopen';
// cspell:ignore fadeblack fadewhite wipeleft wiperight slideleft slideright circleopen: tipos de transición de FFmpeg

export interface Transition {
  id: string;
  track: string;
  a: string;
  b: string;
  type: TransitionType;
  duration: number;
}

export interface Doc {
  version: 2 | 3;
  name: string;
  sample_rate: 48000;
  canvas: Canvas;
  tracks: Track[];
  clips: Clip[];
  markers: Marker[];
  transitions: Transition[];
}

export interface ValidationError {
  code: string;
  id: string;
}

type AudioTrackChanges = Partial<Pick<AudioTrack, 'volume_db' | 'mute' | 'solo' | 'locked'>>;
type VideoTrackChanges = Partial<Pick<VideoTrack, 'opacity' | 'hidden' | 'locked'>>;

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
  | { type: 'setTrack'; id: string; changes: AudioTrackChanges | VideoTrackChanges }
  | { type: 'trimClip'; id: string; edge: 'start' | 'end'; t: number }
  | { type: 'splitAt'; t: number; ids?: string[] }
  | { type: 'deleteClips'; ids: string[]; ripple?: boolean }
  | { type: 'crossfade'; a: string; b: string; d: number }
  | { type: 'linkClips'; ids: string[]; link: string }
  | { type: 'unlinkClips'; ids: string[] };
