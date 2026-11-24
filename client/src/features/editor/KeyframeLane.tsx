import { useRef } from 'react';
import type { PointerEvent as ReactPointerEvent } from 'react';

import { UIButton } from '@/shared/components/atoms/UIButton';
import { UILane } from '@/shared/components/atoms/UILane';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { t } from '@/shared/i18n/t';

import { moveKeyframe, type VisualProperty } from './model/visual';
import { snapCandidates } from './model/timeline';
import { snapTime } from './model/snap';
import { duration } from './model/validate';
import type { Doc, VisualClip } from './model/types';

type Props = {
  doc: Doc;
  clipId: string | null;
  zoom: number;
  magnet: boolean;
  playhead: number;
  locked?: boolean;
  onPreviewDoc: (doc: Doc) => void;
  onCommitPreview: () => void;
  onCancelPreview?: () => void;
};
type Drag = { base: Doc; clip: VisualClip; property: VisualProperty; time: number; left: number; moved: boolean };

const PROPERTY_LABELS: Record<VisualProperty, string> = {
  x: t('editor.inspector.property_x'),
  y: t('editor.inspector.property_y'),
  scale_x: t('editor.inspector.property_scale_x'),
  scale_y: t('editor.inspector.property_scale_y'),
  rotation: t('editor.inspector.property_rotation'),
  opacity: t('editor.inspector.property_opacity'),
  anchor_x: t('editor.inspector.property_anchor_x'),
  anchor_y: t('editor.inspector.property_anchor_y'),
  crop_l: t('editor.inspector.property_crop_l'),
  crop_t: t('editor.inspector.property_crop_t'),
  crop_r: t('editor.inspector.property_crop_r'),
  crop_b: t('editor.inspector.property_crop_b'),
};

function selectedClip(doc: Doc, id: string | null): VisualClip | null {
  const clip = doc.clips.find((item) => item.id === id);
  return clip && (clip.media === 'image' || clip.media === 'video') ? clip : null;
}

/** Carriles compactos de keyframes bajo el clip seleccionado; los rombos respetan el imán de la línea de tiempo. */
export function KeyframeLane({
  doc, clipId, zoom, magnet, playhead, locked = false, onPreviewDoc, onCommitPreview, onCancelPreview = () => undefined,
}: Props): React.JSX.Element | null {
  const dragRef = useRef<Drag | null>(null);
  const selected = selectedClip(doc, clipId);
  if (!selected) return null;
  const entries = Object.entries(selected.keyframes) as Array<[VisualProperty, VisualClip['keyframes'][string]]>;
  if (entries.length === 0) return null;
  const width = Math.max(10, duration(doc)) * zoom;

  function begin(property: VisualProperty, time: number, event: ReactPointerEvent<HTMLButtonElement>): void {
    if (locked || !event.currentTarget.parentElement) return;
    event.preventDefault();
    event.stopPropagation();
    const left = event.currentTarget.parentElement.getBoundingClientRect().left;
    dragRef.current = { base: doc, clip: selected as VisualClip, property, time, left, moved: false };
    event.currentTarget.setPointerCapture?.(event.pointerId);
  }

  function update(event: ReactPointerEvent<HTMLButtonElement>): void {
    const drag = dragRef.current;
    if (!drag) return;
    const requested = Math.max(0, (event.clientX - drag.left) / zoom);
    const snapped = magnet ? snapTime(requested, snapCandidates(drag.base, [drag.clip.id], playhead), zoom) : requested;
    const next = moveKeyframe(drag.base, drag.clip.id, drag.property, drag.time, snapped - drag.clip.start);
    drag.moved = true;
    onPreviewDoc(next);
  }

  function finish(event: ReactPointerEvent<HTMLButtonElement>): void {
    update(event);
    const drag = dragRef.current;
    dragRef.current = null;
    if (drag?.moved) onCommitPreview();
  }

  return (
    <UIStack role="group" aria-label={t('editor.keyframe.label')} gap="xs">
      {entries.map(([property, frames]) => (
        <UILane
          key={property}
          role="group"
          aria-label={t('editor.keyframe.lane', { property: PROPERTY_LABELS[property] })}
          className="relative shrink-0"
          style={{ width: `${width}px`, height: '32px' }}
        >
          {frames.map((frame, index) => (
            <UIButton
              key={`${property}-${index}`}
              aria-label={t('editor.keyframe.point', { property: PROPERTY_LABELS[property], time: String(frame.t) })}
              icon="keyframe"
              variant="ghost"
              disabled={locked}
              className="absolute top-0 size-8 min-h-0 -translate-x-1/2 p-0"
              style={{ left: `${(selected.start + frame.t) * zoom}px` }}
              onPointerDown={(event) => begin(property, frame.t, event)}
              onPointerMove={update}
              onPointerUp={finish}
              onPointerCancel={() => {
                if (dragRef.current?.moved) onCancelPreview();
                dragRef.current = null;
              }}
            />
          ))}
        </UILane>
      ))}
    </UIStack>
  );
}
