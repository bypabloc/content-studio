import { useQuery } from '@tanstack/react-query';

import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { t } from '@/shared/i18n/t';

import { type SelectOption, UIRecommendedSelect } from '../UIRecommendedSelect';

type LlmStatus = components['schemas']['LlmStatus'];

/**
 * El modelo del asistente (spec 021, D-5), con el mismo patrón que `UIWhisperModelSelect`: ★ en el recomendado,
 * recuerda la elección en `select.llm.model` y dice el tamaño y si está instalado.
 */
export function UILlmModelSelect(): React.JSX.Element {
  const api = useApi();
  const status = useQuery({ queryKey: ['llm', 'status'], queryFn: () => api.get<LlmStatus>('/llm/status') });
  const options: SelectOption[] = (status.data?.models ?? []).map((model) => ({
    value: model.model,
    label: model.model,
    recommended: model.recommended,
    hint: t('llm.model.hint', { size: model.size_gb, state: model.installed ? t('llm.model.installed') : t('llm.model.missing') }),
  }));
  return <UIRecommendedSelect settingKey="select.llm.model" label={t('llm.settings.model')} options={options} />;
}
