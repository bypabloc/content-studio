import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { t } from '@/shared/i18n/t';

import { destinationsFor, sendTo, type MediaType, type SendDestination } from './sendTo';

export function SendToActions({ path, type }: { path: string; type: MediaType }): React.JSX.Element {
  const labels: Record<SendDestination, string> = {
    convert: t('convert.submit'),
    normalize: t('normalize.submit'),
    subtitles: t('subtitles.home.create'),
    mix: t('mix.title'),
  };
  return (
    <UIStack role="group" aria-label={t('editor.send_to')} direction="row" gap="sm">
      {destinationsFor(type).map((destination) => (
        <UIButton key={destination} variant="secondary" onClick={() => sendTo(destination, path)}>
          {labels[destination]}
        </UIButton>
      ))}
    </UIStack>
  );
}
