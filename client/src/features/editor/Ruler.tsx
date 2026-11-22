import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';

import { gridStep } from './model/snap';
import type { Marker } from './model/types';

type Props = { duration: number; zoom: number; playhead: number; markers: Marker[] };

const MAX_TICKS = 120;

/** Regla horizontal con marcas, marcadores y el cabezal de reproducción. */
export function Ruler({ duration, zoom, playhead, markers }: Props): React.JSX.Element {
  const baseStep = gridStep(zoom);
  const step = baseStep * Math.max(1, Math.ceil(duration / baseStep / MAX_TICKS));
  const count = Math.floor(duration / step);
  const width = duration * zoom;

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
          role="note"
          aria-label={marker.label}
          className="absolute top-0 z-10 h-full border-l-2 px-1"
          style={{ left: `${marker.t * zoom}px`, borderColor: marker.color, color: marker.color }}
        >
          <UIText variant="caption">{marker.label}</UIText>
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
