import { useEffect, useRef, useState } from 'react';
import type { PointerEvent as ReactPointerEvent } from 'react';

import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICanvas } from '@/shared/components/atoms/UICanvas';
import { UIImage } from '@/shared/components/atoms/UIImage';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';

import { writeVisualValue, type VisualProperty } from '../model/visual';
import type { Doc, VisualClip } from '../model/types';
import { clipProperty } from './compositor';
import { useLayerSources } from './useLayerSources';
import { createCompositor } from './webgl';

type Mode = 'move' | 'scale' | 'rotate' | 'crop';
type Props = {
  doc: Doc;
  path: string;
  time: number;
  selectedClipId: string | null;
  onPreviewDoc: (doc: Doc) => void;
  onCommitPreview: () => void;
  onCancelPreview?: () => void;
};
type Drag = {
  mode: Mode;
  base: Doc;
  clip: VisualClip;
  x: number;
  y: number;
  width: number;
  height: number;
  startAngle: number;
  values: Record<VisualProperty, number>;
  moved: boolean;
};

const PROPERTIES: VisualProperty[] = [
  'x', 'y', 'scale_x', 'scale_y', 'rotation', 'opacity', 'anchor_x', 'anchor_y',
  'crop_l', 'crop_t', 'crop_r', 'crop_b',
];

function selectedClip(doc: Doc, id: string | null): VisualClip | null {
  const clip = doc.clips.find((item) => item.id === id);
  return clip && (clip.media === 'image' || clip.media === 'video') ? clip : null;
}

function cropValue(clip: VisualClip, edge: 'l' | 't' | 'r' | 'b'): number {
  return clip.transform.crop[edge];
}

function propertyValue(clip: VisualClip, property: VisualProperty, time: number): number {
  const fallback = property.startsWith('crop_') ? cropValue(clip, property.slice(-1) as 'l' | 't' | 'r' | 'b') : clip.transform[property as keyof Omit<VisualClip['transform'], 'crop'>];
  return clipProperty(clip, property, time, fallback);
}

/** Vista WebGL del lienzo con guías y asas para transformar el clip seleccionado. */
export function Viewer({
  doc, path, time, selectedClipId, onPreviewDoc, onCommitPreview, onCancelPreview = () => undefined,
}: Props): React.JSX.Element {
  const api = useApi();
  const sources = useLayerSources(doc, path, api);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const compositorRef = useRef<ReturnType<typeof createCompositor> | null>(null);
  const dragRef = useRef<Drag | null>(null);
  const [webglError, setWebglError] = useState(false);
  const [sourceRevision, setSourceRevision] = useState(0);
  const [showExactFrame, setShowExactFrame] = useState(false);
  const sourceSignature = JSON.stringify([
    path,
    doc.clips.flatMap((item) =>
      item.media === 'image' || item.media === 'video' ? [[item.id, item.media, item.src]] : [],
    ),
  ]);
  const clip = selectedClip(doc, selectedClipId);
  const locked = clip ? doc.tracks.find((track) => track.id === clip.track)?.locked ?? true : true;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    try {
      const compositor = createCompositor(canvas);
      compositorRef.current = compositor;
      return () => {
        compositor.destroy();
        compositorRef.current = null;
      };
    } catch {
      const frame = window.requestAnimationFrame(() => setWebglError(true));
      return () => window.cancelAnimationFrame(frame);
    }
  }, []);

  useEffect(() => {
    compositorRef.current?.render(doc, time, sources);
  }, [doc, sources, sourceRevision, time]);

  useEffect(() => {
    let active = true;
    const listeners: Array<[EventTarget, string, () => void]> = [];
    const refresh = () => {
      if (active) setSourceRevision((revision) => revision + 1);
    };
    const [, descriptors] = JSON.parse(sourceSignature) as [string, Array<[string, 'image' | 'video', string]>];
    for (const [id] of descriptors) {
      const source = sources.get(id);
      if (!source) continue;
      const events = source instanceof HTMLVideoElement ? ['loadeddata', 'seeked'] : ['load'];
      for (const event of events) {
        source.addEventListener(event, refresh);
        listeners.push([source, event, refresh]);
      }
    }
    return () => {
      active = false;
      for (const [target, event, listener] of listeners) target.removeEventListener(event, listener);
    };
  }, [sourceSignature, sources]);

  function begin(mode: Mode, event: ReactPointerEvent<HTMLButtonElement>): void {
    if (!clip || locked || !stageRef.current) return;
    event.preventDefault();
    event.stopPropagation();
    const rect = stageRef.current.getBoundingClientRect();
    const actualMode = event.altKey ? 'crop' : mode;
    const values = Object.fromEntries(PROPERTIES.map((property) => [property, propertyValue(clip, property, time)])) as Record<VisualProperty, number>;
    const startAngle = Math.atan2(event.clientY - (rect.top + rect.height / 2), event.clientX - (rect.left + rect.width / 2));
    dragRef.current = {
      mode: actualMode, base: doc, clip, x: event.clientX, y: event.clientY,
      width: rect.width || doc.canvas.width, height: rect.height || doc.canvas.height, startAngle, values, moved: false,
    };
    event.currentTarget.setPointerCapture?.(event.pointerId);
  }

  function update(event: ReactPointerEvent<HTMLButtonElement>): void {
    const drag = dragRef.current;
    if (!drag) return;
    const dx = (event.clientX - drag.x) / drag.width;
    const dy = (event.clientY - drag.y) / drag.height;
    let next = drag.base;
    const write = (property: VisualProperty, value: number) => {
      next = writeVisualValue(next, drag.clip.id, property, time, value);
    };
    if (drag.mode === 'move') {
      write('x', drag.values.x + dx * drag.base.canvas.width);
      write('y', drag.values.y + dy * drag.base.canvas.height);
    } else if (drag.mode === 'scale') {
      if (event.shiftKey) {
        const factor = Math.max(0.01, 1 + (dx + dy) / 2);
        write('scale_x', drag.values.scale_x * factor);
        write('scale_y', drag.values.scale_y * factor);
      } else {
        write('scale_x', Math.max(0.01, drag.values.scale_x + dx * 2));
        write('scale_y', Math.max(0.01, drag.values.scale_y + dy * 2));
      }
    } else if (drag.mode === 'rotate') {
      const rect = stageRef.current?.getBoundingClientRect();
      if (!rect) return;
      const angle = Math.atan2(event.clientY - (rect.top + rect.height / 2), event.clientX - (rect.left + rect.width / 2));
      write('rotation', drag.values.rotation + ((angle - drag.startAngle) * 180) / Math.PI);
    } else {
      write('crop_l', Math.max(0, Math.min(0.99 - drag.values.crop_r, drag.values.crop_l + dx)));
    }
    drag.moved = true;
    onPreviewDoc(next);
  }

  function finish(event: ReactPointerEvent<HTMLButtonElement>): void {
    update(event);
    const drag = dragRef.current;
    dragRef.current = null;
    if (drag?.moved) onCommitPreview();
  }

  function cancel(): void {
    if (dragRef.current?.moved) onCancelPreview();
    dragRef.current = null;
  }

  const clipStyle = clip
    ? {
        left: `${50 + (clip.transform.x / doc.canvas.width) * 100}%`,
        top: `${50 + (clip.transform.y / doc.canvas.height) * 100}%`,
        width: `${Math.min(80, 40 * clip.transform.scale_x)}%`,
        height: `${Math.min(80, 40 * clip.transform.scale_y)}%`,
        transform: `translate(-50%, -50%) rotate(${clip.transform.rotation}deg)`,
      }
    : undefined;

  return (
    <UIStack role="group" aria-label={t('editor.viewer.label')} gap="xs">
      <UIText variant="heading">{t('editor.viewer.label')}</UIText>
      <UIStack
        ref={stageRef}
        role="group"
        aria-label={t('editor.viewer.stage')}
        className="relative mx-auto w-full max-w-4xl overflow-hidden bg-black"
        style={{ aspectRatio: `${doc.canvas.width} / ${doc.canvas.height}` }}
      >
        <UICanvas
          ref={canvasRef}
          aria-label={t('editor.viewer.canvas')}
          className="absolute inset-0 size-full"
          style={{ background: doc.canvas.background }}
        />
        <UIStack role="img" aria-label={t('editor.viewer.safe_area')} className="pointer-events-none absolute inset-[5%] border border-white/60">
          <UIStack className="absolute inset-[5%] border border-white/40" />
          <UIStack className="absolute inset-[15%] border-y border-white/30" />
        </UIStack>
        {clip ? (
          <UIStack className="pointer-events-none absolute inset-0">
            <UIButton
              aria-label={t('editor.viewer.move')}
              variant="ghost"
              disabled={locked}
              className="pointer-events-auto absolute border-2 border-primary bg-primary/10 p-0"
              style={clipStyle}
              onPointerDown={(event) => begin('move', event)}
              onPointerMove={update}
              onPointerUp={finish}
              onPointerCancel={cancel}
            />
            <UIButton
              aria-label={t('editor.viewer.rotate')}
              icon="retry"
              variant="secondary"
              disabled={locked}
              className="pointer-events-auto absolute left-1/2 top-[8%] size-9 min-h-0 -translate-x-1/2 p-0"
              onPointerDown={(event) => begin('rotate', event)}
              onPointerMove={update}
              onPointerUp={finish}
              onPointerCancel={cancel}
            />
            <UIButton
              aria-label={t('editor.viewer.scale')}
              icon="arrow-down-up"
              variant="secondary"
              disabled={locked}
              className="pointer-events-auto absolute bottom-[18%] right-[18%] size-9 min-h-0 p-0"
              onPointerDown={(event) => begin('scale', event)}
              onPointerMove={update}
              onPointerUp={finish}
              onPointerCancel={cancel}
            />
            <UIButton
              aria-label={t('editor.viewer.crop')}
              icon="scissors"
              variant="secondary"
              disabled={locked}
              className="pointer-events-auto absolute left-[18%] top-[18%] size-9 min-h-0 p-0"
              onPointerDown={(event) => begin('crop', event)}
              onPointerMove={update}
              onPointerUp={finish}
              onPointerCancel={cancel}
            />
          </UIStack>
        ) : null}
      </UIStack>
      <UIButton
        variant="secondary"
        aria-pressed={showExactFrame}
        onClick={() => setShowExactFrame((visible) => !visible)}
      >
        {t('editor.viewer.exact_frame')}
      </UIButton>
      {showExactFrame ? (
        <UIImage
          alt={t('editor.viewer.exact_frame_image', { time: time.toFixed(2) })}
          crossOrigin="anonymous"
          width={doc.canvas.width}
          height={doc.canvas.height}
          className="mx-auto max-h-72 max-w-full object-contain"
          src={api.queryUrl('/editor/projects/frame', { path, t: String(time) })}
        />
      ) : null}
      {webglError ? <UIText variant="caption">{t('editor.viewer.webgl_error')}</UIText> : null}
    </UIStack>
  );
}
