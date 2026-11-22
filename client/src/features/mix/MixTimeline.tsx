import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { t } from '@/shared/i18n/t';

export interface MixTimelineProps {
  regions: [number, number][];
  duration: number;
  onChange: (regions: [number, number][]) => void;
}

const STEP = 0.1; // segundos que mueve una flecha

const round = (value: number): number => Math.round(value * 10) / 10;

/**
 * Las regiones de ducking (spec 016, D-4): cada una es un botón que se mueve con las flechas en pasos de 0,1 s (sin
 * salirse de la mezcla) y se borra con la tecla Suprimir. Arrastrar con el ratón queda para una revisión (PENDING).
 */
export function MixTimeline({ regions, duration, onChange }: MixTimelineProps): React.JSX.Element {
  function replace(index: number, next: [number, number] | null): void {
    onChange(
      next ? regions.map((region, i) => (i === index ? next : region)) : regions.filter((_, i) => i !== index),
    );
  }

  function onKeyDown(index: number, event: React.KeyboardEvent<HTMLButtonElement>): void {
    if (event.key === 'Delete' || event.key === 'Backspace') {
      event.preventDefault();
      replace(index, null);
      return;
    }
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return;
    event.preventDefault();
    const [start, end] = regions[index];
    const length = end - start;
    if (duration <= length) return; // región más larga que la mezcla (o duración aún no conocida): no hay adónde moverla
    const step = event.key === 'ArrowRight' ? STEP : -STEP;
    const moved = Math.min(Math.max(0, start + step), duration - length);
    replace(index, [round(moved), round(moved + length)]);
  }

  return (
    <UIStack role="list" aria-label={t('mix.timeline.label')} gap="sm">
      {regions.map(([start, end], index) => (
        <UIStack key={`${start}-${end}-${index}`} role="listitem">
          <UIButton
            variant="ghost"
            aria-label={t('mix.region.label', { n: index + 1 })}
            onKeyDown={(event) => onKeyDown(index, event)}
          >
            {t('mix.region.span', { start: start.toFixed(1), end: end.toFixed(1) })}
          </UIButton>
        </UIStack>
      ))}
    </UIStack>
  );
}
