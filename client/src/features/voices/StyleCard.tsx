import { useApi } from '@/shared/api/context';
import { UICard } from '@/shared/components/atoms/UICard';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { label, t } from '@/shared/i18n/t';
import { Player } from '@/shared/media/Player';
import { useMediaPeaks } from '@/shared/media/useMediaInfo';
import type { StyleStatus } from './useVoices';

/**
 * Un estilo de la ficha: su nombre, si tiene referencia elegida (con su reproductor, que pide los picos al server) y
 * cuántas tomas tiene (spec 010, D-6).
 */
export function StyleCard({ item }: { item: StyleStatus }) {
  const api = useApi();
  const id = `style-${item.style}`;
  const peaks = useMediaPeaks(item.reference ?? '');
  return (
    <UICard aria-labelledby={id}>
      <UIText variant="heading" id={id}>
        {label('narration.style', item.style)}
      </UIText>
      <UIStack gap="sm" className="mt-3">
        <UIText variant="caption">{item.chosen ? t('voices.style.chosen') : t('voices.style.missing')}</UIText>
        <UIText variant="caption">{t('voices.takes', { count: item.takes })}</UIText>
      </UIStack>
      {item.reference && peaks.data ? (
        <UIStack className="mt-4">
          <Player src={api.fileUrl(item.reference)} peaks={peaks.data.peaks} />
        </UIStack>
      ) : null}
    </UICard>
  );
}
