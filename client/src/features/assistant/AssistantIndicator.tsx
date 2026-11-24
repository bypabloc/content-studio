import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';

import { useAssistantStatus } from './useAssistant';

/** «Asistente cargado (se libera en 1:45)» en la cola, mientras el modelo sigue en la GPU (spec 021, D-2). */
export function AssistantIndicator(): React.JSX.Element | null {
  const status = useAssistantStatus();
  const loaded = status.data?.loaded;
  if (!loaded) return null;
  const seconds = Math.round(status.data?.release_in ?? 0);
  const time = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
  return (
    <UIText variant="caption" role="status">
      {t('llm.loaded', { model: loaded, time })}
    </UIText>
  );
}
