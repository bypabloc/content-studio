import { useQuery } from '@tanstack/react-query';

import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { t } from '@/shared/i18n/t';

import { type SelectOption, UIRecommendedSelect } from '../UIRecommendedSelect';

type EngineInfo = components['schemas']['EngineInfo'];

/**
 * El modelo de faster-whisper para transcribir (spec 013, D-1, AC-9): ★ en el recomendado, recuerda la última elección y
 * muestra el tamaño de cada modelo con si ya está descargado (si no, la descarga entra en el trabajo). Lo reusa la 014.
 */
export function UIWhisperModelSelect(): React.JSX.Element {
  const api = useApi();
  const engines = useQuery({ queryKey: ['engines'], queryFn: () => api.get<EngineInfo[]>('/engines') });
  const models = engines.data?.find((engine) => engine.engine === 'faster-whisper')?.models ?? [];
  const options: SelectOption[] = models.map((model) => ({
    value: model.model,
    label: model.model,
    recommended: model.recommended,
    hint: `${t('whisper.size', { size: model.size_gb })} · ${model.downloaded ? t('whisper.downloaded') : t('whisper.not_downloaded')}`,
  }));

  return <UIRecommendedSelect settingKey="select.whisper.model" label={t('whisper.model')} options={options} />;
}
