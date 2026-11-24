import { clipLength } from '../model/validate';
import { valueAt } from '../model/keyframes';
import type { Canvas, Doc, Transition, VideoTrack, VisualClip } from '../model/types';
import { transitionProgress } from './transitions';
import type { LayerSourceLookup } from './useLayerSources';

export type ClipLayer = { kind: 'clip'; track: VideoTrack; trackId: string; clip: VisualClip; clipId: string };
export type TransitionLayer = {
  kind: 'transition';
  track: VideoTrack;
  trackId: string;
  transition: Transition;
  clipIds: [string, string];
  from: VisualClip;
  to: VisualClip;
  progress: number;
};
export type PreviewLayer = ClipLayer | TransitionLayer;
export type Compositor = {
  render: (doc: Doc, time: number, sources: LayerSourceLookup) => void;
  destroy: () => void;
};

export function clipProperty(clip: VisualClip, key: string, time: number, fallback: number): number {
  return valueAt(clip.keyframes[key] ?? [], Math.max(0, time - clip.start), fallback);
}

export function clipCrop(clip: VisualClip, time: number): { l: number; t: number; r: number; b: number } {
  const crop = clip.transform.crop;
  return {
    l: clipProperty(clip, 'crop_l', time, crop.l),
    t: clipProperty(clip, 'crop_t', time, crop.t),
    r: clipProperty(clip, 'crop_r', time, crop.r),
    b: clipProperty(clip, 'crop_b', time, crop.b),
  };
}

export function hasAnimatedCrop(clip: VisualClip): boolean {
  return ['l', 't', 'r', 'b'].some((edge) => (clip.keyframes['crop_' + edge] ?? []).length > 0);
}

/** Matriz source-pixel → WebGL clip-space con el mismo orden de rotación y escala del render FFmpeg. */
export function buildLayerMatrix(
  clip: VisualClip,
  _track: VideoTrack,
  canvas: Canvas,
  sourceSize: { width: number; height: number },
  time: number,
): Float32Array {
  const { width, height } = sourceSize;
  const crop = clipCrop(clip, time);
  const dynamicCrop = hasAnimatedCrop(clip);
  const cropWidth = width * (1 - crop.l - crop.r);
  const cropHeight = height * (1 - crop.t - crop.b);
  const centerX = dynamicCrop ? width / 2 : crop.l * width + cropWidth / 2;
  const centerY = dynamicCrop ? height / 2 : crop.t * height + cropHeight / 2;
  const anchorX = clipProperty(clip, 'anchor_x', time, clip.transform.anchor_x);
  const anchorY = clipProperty(clip, 'anchor_y', time, clip.transform.anchor_y);
  const dx = dynamicCrop
    ? (crop.l + anchorX * (1 - crop.l - crop.r) - 0.5) * width
    : (anchorX - 0.5) * cropWidth;
  const dy = dynamicCrop
    ? (crop.t + anchorY * (1 - crop.t - crop.b) - 0.5) * height
    : (anchorY - 0.5) * cropHeight;
  const rotation = (clipProperty(clip, 'rotation', time, clip.transform.rotation) * Math.PI) / 180;
  const scaleX = clipProperty(clip, 'scale_x', time, clip.transform.scale_x);
  const scaleY = clipProperty(clip, 'scale_y', time, clip.transform.scale_y);
  const x = clipProperty(clip, 'x', time, clip.transform.x);
  const y = clipProperty(clip, 'y', time, clip.transform.y);
  const cos = Math.cos(rotation);
  const sin = Math.sin(rotation);
  const anchorDx = (dx * cos - dy * sin) * scaleX;
  const anchorDy = (dx * sin + dy * cos) * scaleY;
  const targetX = canvas.width / 2 + x - anchorDx;
  const targetY = canvas.height / 2 + y - anchorDy;
  const sourceOffsetX = (centerX * cos - centerY * sin) * scaleX;
  const sourceOffsetY = (centerX * sin + centerY * cos) * scaleY;
  return new Float32Array([
    (2 * cos * scaleX) / canvas.width,
    (-2 * sin * scaleY) / canvas.height,
    0,
    (-2 * sin * scaleX) / canvas.width,
    (-2 * cos * scaleY) / canvas.height,
    0,
    (2 * (targetX - sourceOffsetX)) / canvas.width - 1,
    1 - (2 * (targetY - sourceOffsetY)) / canvas.height,
    1,
  ]);
}

/** Planifica las capas visibles en el orden inferior-superior y agrupa transiciones activas por pista. */
export function orderedLayers(doc: Doc, time: number): PreviewLayer[] {
  const result: PreviewLayer[] = [];
  for (const track of doc.tracks) {
    if (track.kind !== 'video' || track.hidden || track.opacity <= 0) continue;
    const clips = doc.clips
      .filter((clip): clip is VisualClip => 'media' in clip && clip.track === track.id)
      .sort((a, b) => a.start - b.start);
    const active = new Set(clips.filter((clip) => clip.start <= time && time < clip.start + clipLength(clip)));
    for (let index = 0; index < clips.length; index += 1) {
      const from = clips[index];
      if (!active.has(from)) continue;
      const to = clips[index + 1];
      const transition = to && doc.transitions.find((item) => item.track === track.id && item.a === from.id && item.b === to.id);
      const overlapStart = to?.start ?? 0;
      const overlapEnd = from.start + clipLength(from);
      if (to && active.has(to) && transition && time >= overlapStart && time < overlapEnd) {
        result.push({
          kind: 'transition',
          track,
          trackId: track.id,
          transition,
          clipIds: [from.id, to.id],
          from,
          to,
          progress: transitionProgress(time, overlapStart, transition.duration),
        });
        active.delete(to);
      } else {
        result.push({ kind: 'clip', track, trackId: track.id, clip: from, clipId: from.id });
      }
    }
  }
  return result;
}
