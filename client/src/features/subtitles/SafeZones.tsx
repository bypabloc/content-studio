import { UIStack } from '@/shared/components/atoms/UIStack';
import { t } from '@/shared/i18n/t';

import zones from './safe-zones.json';

export type ZoneName = keyof typeof zones;
export interface ZoneBox {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

/** Los márgenes de una plataforma, en porcentaje del cuadro (datos en safe-zones.json, D-9). */
export function zoneBox(name: ZoneName): ZoneBox {
  return zones[name];
}

/** La zona segura de una plataforma, dibujada sobre la vista previa. Sin zona, no dibuja nada. */
export function SafeZones({ zone }: { zone: ZoneName | null }): React.JSX.Element | null {
  if (!zone) return null;
  const box = zoneBox(zone);
  const labels = { reels: t('subtitles.zones.reels'), tiktok: t('subtitles.zones.tiktok'), shorts: t('subtitles.zones.shorts') };
  return (
    <UIStack
      role="group"
      aria-label={labels[zone]}
      className="pointer-events-none absolute border border-dashed border-primary/70"
      style={{ top: `${box.top}%`, bottom: `${box.bottom}%`, left: `${box.left}%`, right: `${box.right}%` }}
    />
  );
}
