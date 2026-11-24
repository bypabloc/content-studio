import { UICheckbox } from '@/shared/components/atoms/UICheckbox';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UILlmModelSelect } from '@/shared/components/molecules/UILlmModelSelect';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';

const IDLE_MINUTES = [1, 2, 5, 10];

/**
 * Ajustes > Asistente (spec 021, D-5): mostrar u ocultar los botones de IA, el modelo ★ y cuánto espera el modelo
 * caliente antes de liberar la GPU.
 */
export function AssistantSettings(): React.JSX.Element {
  const [enabled, setEnabled] = useSetting('llm.enabled', true);
  const [idle, setIdle] = useSetting('llm.idle_seconds', 120);
  return (
    <UIStack gap="md">
      <UIText variant="heading">{t('llm.settings.title')}</UIText>
      <UICheckbox label={t('llm.settings.enabled')} checked={enabled} onChange={setEnabled} />
      <UILlmModelSelect />
      <UISelect
        label={t('llm.settings.idle')}
        value={String(idle)}
        options={IDLE_MINUTES.map((minutes) => ({ value: String(minutes * 60), label: t('llm.settings.idle_option', { minutes }) }))}
        onChange={(value) => setIdle(Number(value))}
      />
    </UIStack>
  );
}
