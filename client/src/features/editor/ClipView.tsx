import { useRef } from 'react';
import type { PointerEvent as ReactPointerEvent, KeyboardEvent } from 'react';

import { useApi } from '@/shared/api/context';
import type { Api } from '@/shared/api/client';
import { UIClip } from '@/shared/components/atoms/UIClip';
import { UIImage } from '@/shared/components/atoms/UIImage';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { t } from '@/shared/i18n/t';

import { apply } from './model/ops';
import { gridStep, snapTime } from './model/snap';
import { clipLength } from './model/validate';
import { moveClips, snapCandidates } from './model/timeline';
import type { Clip, Doc } from './model/types';

type Props = {
  clip: Clip;
  doc: Doc;
  selected: boolean;
  selectedIds: string[];
  zoom: number;
  magnet: boolean;
  playhead: number;
  locked: boolean;
  onSelect: (ids: string[]) => void;
  onPreview: (doc: Doc) => void;
  onCommitPreview: () => void;
  onCancelPreview: () => void;
};

type Drag = {
  base: Doc;
  clip: Clip;
  length: number;
  ids: string[];
  mode: 'move' | 'start' | 'end';
  originX: number;
  moved: boolean;
};

const DRAG_THRESHOLD_PX = 2;

function sourceName(src: string): string {
  return src.split(/[\\/]/).pop() || src;
}

function snapGrid(time: number, zoom: number): number[] {
  const step = gridStep(zoom);
  const first = Math.max(0, Math.floor(time / step) - 2);
  return Array.from({ length: 5 }, (_, index) => (first + index) * step);
}

/** Representación y edición por arrastre de un clip de audio. */
export function ClipView({
  clip,
  doc,
  selected,
  selectedIds,
  zoom,
  magnet,
  playhead,
  locked,
  onSelect,
  onPreview,
  onCommitPreview,
  onCancelPreview,
}: Props): React.JSX.Element {
  const api = useApi();
  const dragRef = useRef<Drag | null>(null);
  const length = clipLength(clip);
  const source = sourceName(clip.src);
  const label = t('editor.clip.label', { source, start: clip.start.toFixed(1), end: (clip.start + length).toFixed(1) });
  const width = length * zoom;
  const thumbnails = videoThumbnails(clip, zoom, api.queryUrl);

  function beginDrag(mode: Drag['mode'], event: ReactPointerEvent<HTMLElement>): void {
    event.stopPropagation();
    event.preventDefault();
    if (!selected) onSelect([clip.id]);
    if (locked) return;
    const ids = selected && selectedIds.includes(clip.id) ? selectedIds : [clip.id];
    dragRef.current = { base: doc, clip, length, ids, mode, originX: event.clientX, moved: false };
    event.currentTarget.setPointerCapture?.(event.pointerId);
  }

  function updateDrag(event: ReactPointerEvent<HTMLElement>): void {
    const drag = dragRef.current;
    if (!drag) return;
    const deltaPx = event.clientX - drag.originX;
    if (Math.abs(deltaPx) < DRAG_THRESHOLD_PX) return;
    const delta = deltaPx / zoom;
    const cursor =
      drag.mode === 'start'
        ? drag.clip.start + delta
        : drag.mode === 'end'
          ? drag.clip.start + drag.length + delta
          : drag.clip.start + delta;
    const excluded = drag.mode === 'move' ? drag.ids : [clip.id];
    const time = magnet
      ? snapTime(cursor, [...snapGrid(cursor, zoom), ...snapCandidates(drag.base, excluded, playhead)], zoom)
      : cursor;
    try {
      const next =
        drag.mode === 'move'
          ? moveClips(drag.base, drag.ids, time - drag.clip.start)
          : apply(drag.base, { type: 'trimClip', id: drag.clip.id, edge: drag.mode, t: time });
      drag.moved = true;
      onPreview(next);
    } catch {
      // El borde puede salir del rango de la fuente mientras se arrastra; se conserva el último preview válido.
    }
  }

  function finishDrag(event: ReactPointerEvent<HTMLElement>): void {
    updateDrag(event);
    const drag = dragRef.current;
    dragRef.current = null;
    if (drag?.moved) onCommitPreview();
  }

  function cancelDrag(): void {
    const drag = dragRef.current;
    dragRef.current = null;
    if (drag?.moved) onCancelPreview();
  }

  function trimByKey(mode: 'start' | 'end', event: KeyboardEvent<HTMLDivElement>): void {
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
    event.preventDefault();
    const direction = event.key === 'ArrowRight' ? 1 : -1;
    const requested = (mode === 'start' ? clip.start : clip.start + length) + direction * 0.1;
    const time = magnet
      ? snapTime(requested, [...snapGrid(requested, zoom), ...snapCandidates(doc, [clip.id], playhead)], zoom)
      : requested;
    try {
      onPreview(apply(doc, { type: 'trimClip', id: clip.id, edge: mode, t: time }));
      onCommitPreview();
    } catch {
      // Se ignora el paso de teclado si deja una duración inválida.
    }
  }

  const start = clip.start;
  const end = clip.start + length;

  return (
    <UIStack
      role="group"
      aria-label={label}
      className="absolute top-2 h-16"
      style={{ left: `${start * zoom}px`, width: `${width}px` }}
    >
      <UIClip
        aria-label={label}
        aria-pressed={selected}
        className={selected ? 'ring-2 ring-primary' : ''}
        style={{ left: 0, top: 0, width: '100%', height: '100%' }}
        onClick={() => {
          if (!selected) onSelect([clip.id]);
        }}
        onPointerDown={(event) => beginDrag('move', event)}
        onPointerMove={updateDrag}
        onPointerUp={finishDrag}
        onPointerCancel={cancelDrag}
      >
        {thumbnails.map((thumbnail) => (
          <UIImage
            key={thumbnail.time}
            alt=""
            aria-hidden="true"
            src={thumbnail.src}
            className="pointer-events-none absolute top-0 h-full object-cover opacity-50"
            style={{ left: `${thumbnail.left}%`, width: `${thumbnail.width}%` }}
          />
        ))}
        {source}
      </UIClip>
      <UIStack
        role="slider"
        aria-label={t('editor.clip.trim_start', { source })}
        aria-valuemin={0}
        aria-valuemax={end}
        aria-valuenow={start}
        tabIndex={0}
        className="absolute left-0 top-0 z-10 h-full w-3 cursor-ew-resize opacity-0 hover:opacity-100 focus-visible:opacity-100"
        onPointerDown={(event) => beginDrag('start', event)}
        onPointerMove={updateDrag}
        onPointerUp={finishDrag}
        onPointerCancel={cancelDrag}
        onKeyDown={(event) => trimByKey('start', event)}
      />
      <UIStack
        role="slider"
        aria-label={t('editor.clip.trim_end', { source })}
        aria-valuemin={start}
        aria-valuemax={Number.MAX_SAFE_INTEGER}
        aria-valuenow={end}
        tabIndex={0}
        className="absolute right-0 top-0 z-10 h-full w-3 cursor-ew-resize opacity-0 hover:opacity-100 focus-visible:opacity-100"
        onPointerDown={(event) => beginDrag('end', event)}
        onPointerMove={updateDrag}
        onPointerUp={finishDrag}
        onPointerCancel={cancelDrag}
        onKeyDown={(event) => trimByKey('end', event)}
      />
    </UIStack>
  );
}

function videoThumbnails(clip: Clip, zoom: number, queryUrl: Api['queryUrl']): Array<{ time: number; left: number; width: number; src: string }> {
  if (clip.media !== 'video') return [];
  const length = clipLength(clip);
  const step = Math.max(0.5, length / 12, 100 / zoom);
  const count = Math.max(1, Math.ceil(length / step));
  return Array.from({ length: count }, (_, index) => {
    const offset = index * step;
    const segment = Math.min(step, length - offset);
    const time = clip.src_in + offset;
    return {
      time,
      left: (offset / length) * 100,
      width: (segment / length) * 100,
      src: queryUrl('/media/frame', { path: clip.src, t: String(time) }),
    };
  });
}
