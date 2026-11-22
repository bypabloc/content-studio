import { useState } from 'react';

import { UIField } from '@/shared/components/molecules/UIField';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';

import { gridStep } from './model/snap';
import type { Marker } from './model/types';

type Props = {
  duration: number;
  zoom: number;
  playhead: number;
  markers: Marker[];
  selectedMarker?: string | null;
  onMarkerSelect?: (id: string) => void;
  onMarkerRename?: (id: string, label: string) => void;
};

const MAX_TICKS = 120;

/** Regla horizontal con marcas, marcadores y el cabezal de reproducción. */
export function Ruler({
  duration,
  zoom,
  playhead,
  markers,
  selectedMarker = null,
  onMarkerSelect = () => undefined,
  onMarkerRename,
}: Props): React.JSX.Element {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const baseStep = gridStep(zoom);
  const step = baseStep * Math.max(1, Math.ceil(duration / baseStep / MAX_TICKS));
  const count = Math.floor(duration / step);
  const width = duration * zoom;

  function saveLabel(id: string): void {
    const label = draft.trim();
    if (label) onMarkerRename?.(id, label);
    setEditingId(null);
  }

  return (
    <UIStack
      role="group"
      aria-label={t('editor.timeline.ruler')}
      className="relative h-9 shrink-0 border-b border-border bg-muted/40"
      style={{ width: `${width}px` }}
    >
      {Array.from({ length: count + 1 }, (_, index) => {
        const time = index * step;
        return (
          <UIStack
            key={time}
            role="presentation"
            className="absolute top-0 h-full border-l border-border/70 pl-1"
            style={{ left: `${time * zoom}px` }}
          >
            <UIText variant="caption">{t('editor.timeline.tick', { time: Number(time.toFixed(2)) })}</UIText>
          </UIStack>
        );
      })}
      {markers.map((marker) => (
        <UIStack
          key={marker.id}
          role={editingId === marker.id ? 'group' : 'button'}
          aria-label={editingId === marker.id ? undefined : marker.label}
          aria-pressed={editingId === marker.id ? undefined : selectedMarker === marker.id}
          tabIndex={editingId === marker.id ? -1 : 0}
          className={`absolute top-0 z-10 h-full border-l-2 px-1 ${selectedMarker === marker.id ? 'bg-primary/10' : ''}`}
          style={{ left: `${marker.t * zoom}px`, borderColor: marker.color, color: marker.color }}
          onClick={() => onMarkerSelect(marker.id)}
          onDoubleClick={(event) => {
            event.stopPropagation();
            setDraft(marker.label);
            setEditingId(marker.id);
          }}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              event.stopPropagation();
              onMarkerSelect(marker.id);
            }
          }}
        >
          {editingId === marker.id ? (
            <UIField
              label={t('editor.marker.rename')}
              hideLabel
              autoFocus
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onBlur={() => saveLabel(marker.id)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  event.preventDefault();
                  event.stopPropagation();
                  saveLabel(marker.id);
                } else if (event.key === 'Escape') {
                  event.preventDefault();
                  event.stopPropagation();
                  setEditingId(null);
                }
              }}
            />
          ) : (
            <UIText variant="caption">{marker.label}</UIText>
          )}
        </UIStack>
      ))}
      <UIStack
        role="img"
        aria-label={t('editor.timeline.position')}
        className="absolute top-0 z-20 h-full border-l-2 border-primary"
        style={{ left: `${playhead * zoom}px` }}
      />
    </UIStack>
  );
}
