import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { LicenseDialog } from '@/shared/components/LicenseDialog';
import { UIRecommendedSelect } from '@/shared/components/molecules/UIRecommendedSelect';
import { label, t } from '@/shared/i18n/t';
import { AdvancedOptions } from './AdvancedOptions';
import { type CatalogEngine, useNarrationChoice } from './useNarrationChoice';

type SettingOut = components['schemas']['SettingOut'];

const acceptedKey = (engine: string) => `narration.license.accepted.${engine}`;

/**
 * Los selectores de la narración: motor, voz, estilo e idioma, con ★ en lo recomendado. Un motor con licencia no
 * comercial pide aceptarla la primera vez (AC-7). «Avanzado» abre lo demás.
 */
export function NarrationOptions() {
  const api = useApi();
  const queryClient = useQueryClient();
  const choice = useNarrationChoice();
  const [advanced, setAdvanced] = useState(false);
  const [pending, setPending] = useState<{ engine: CatalogEngine; answer: (ok: boolean) => void } | null>(null);
  const current = choice.engines.find((engine) => engine.id === choice.model);

  // Pide la licencia solo si el motor no es comercial y aún no se aceptó: la respuesta llega al cerrar el aviso.
  const confirmLicense = async (id: string): Promise<boolean> => {
    const engine = choice.engines.find((item) => item.id === id);
    if (!engine || engine.commercial) return true;
    const key = acceptedKey(id);
    // La caché manda: tras aceptar, no se vuelve a preguntar aunque la API responda otra cosa. Si la API falla, se pregunta.
    const saved = await queryClient
      .ensureQueryData({ queryKey: ['settings', key], queryFn: () => api.get<SettingOut>(`/settings/${key}`) })
      .catch(() => undefined);
    if (saved?.value === true) return true;
    return new Promise<boolean>((answer) => setPending({ engine, answer }));
  };

  // Aceptar guarda la licencia. Si el guardado falla, la elección no se aplica: el aviso se cierra igual.
  const accept = async () => {
    if (!pending) return;
    const { engine, answer } = pending;
    const key = acceptedKey(engine.id);
    setPending(null);
    try {
      await api.put(`/settings/${key}`, { value: true });
      queryClient.setQueryData<SettingOut>(['settings', key], { key, value: true });
      answer(true);
    } catch {
      answer(false);
    }
  };

  const cancel = () => {
    pending?.answer(false);
    setPending(null);
  };

  return (
    <section className="flex flex-col gap-4">
      <UIRecommendedSelect
        settingKey="select.narration.model"
        label={t('narration.options.engine')}
        options={choice.engines.map((engine) => ({
          value: engine.id,
          label: engine.commercial ? engine.id : `${engine.id} (${t('narration.engine.noncommercial')})`,
          recommended: engine.recommended,
          disabled: !engine.installed,
          hint: label('narration.engine', engine.id),
        }))}
        beforeChange={confirmLicense}
      />
      <UIRecommendedSelect
        settingKey="select.narration.voice"
        label={t('narration.options.voice')}
        options={choice.voices.map((voice) => ({ value: voice.id, label: voice.id }))}
      />
      <UIRecommendedSelect
        settingKey="select.narration.style"
        label={t('narration.options.style')}
        options={choice.styles.map((style) => ({
          value: style.id,
          label: label('narration.style', style.id),
          recommended: style.recommended,
        }))}
      />
      <UIRecommendedSelect
        settingKey="select.narration.language"
        label={t('narration.options.language')}
        options={[
          { value: 'es', label: t('narration.language.es'), recommended: true },
          { value: 'en', label: t('narration.language.en') },
        ]}
      />
      <button
        type="button"
        aria-expanded={advanced}
        onClick={() => setAdvanced((open) => !open)}
        className="self-start text-sm text-muted-foreground underline underline-offset-4"
      >
        {t('narration.advanced.toggle')}
      </button>
      {advanced && <AdvancedOptions supportsBatch={current?.batch ?? false} />}
      {pending && (
        <LicenseDialog
          engine={pending.engine.id}
          license={pending.engine.license}
          commercial={pending.engine.commercial}
          onAccept={() => void accept()}
          onCancel={cancel}
        />
      )}
    </section>
  );
}
