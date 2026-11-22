import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { useState } from 'react';

import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UISwitch } from '@/shared/components/atoms/UISwitch';
import { UIField } from '@/shared/components/molecules/UIField';
import { UIRecommendedSelect } from '@/shared/components/molecules/UIRecommendedSelect';
import { UIWhisperModelSelect } from '@/shared/components/molecules/UIWhisperModelSelect';
import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';

import { CleanReview } from './CleanReview';

type Job = components['schemas']['Job'];

const MEDIA_EXTENSIONS = ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac', 'mp4', 'mov', 'mkv', 'webm', 'avi', 'm4v'];

function languageOptions() {
  return [
    { value: 'es', label: t('cleaner.language.es'), recommended: true },
    { value: 'en', label: t('cleaner.language.en') },
    { value: 'pt', label: t('cleaner.language.pt') },
    { value: 'fr', label: t('cleaner.language.fr') },
    { value: 'de', label: t('cleaner.language.de') },
    { value: 'it', label: t('cleaner.language.it') },
    { value: 'auto', label: t('cleaner.language.auto') },
  ];
}

function baseName(path: string): string {
  return path.split(/[\\/]/).pop() ?? path;
}

// Un número escrito a medias ('' o '-') cuenta como 0, no como NaN.
function number(raw: string): number {
  const value = Number(raw);
  return raw !== '' && Number.isFinite(value) ? value : 0;
}

/** El estado de un análisis en el lote. Con «Aplicar todos sin revisar», el render encadenado manda sobre el análisis. */
function statusOf(job: Job, renders: Job[]): { text: string; review: boolean } {
  const params = job.params as { auto_render?: boolean };
  if (job.status === 'queued') return { text: t('cleaner.status.queued'), review: false };
  if (job.status === 'running') return { text: t('cleaner.status.running', { percent: Math.round(job.progress * 100) }), review: false };
  if (job.status === 'cancelled') return { text: t('cleaner.status.cancelled'), review: false };
  if (job.status === 'error') return { text: t('cleaner.status.error'), review: false };
  if (!params.auto_render) return { text: t('cleaner.status.review'), review: true };
  const render = renders.find((item) => (item.params as { analysis?: string }).analysis === job.output_dir);
  if (render?.status === 'done') return { text: t('cleaner.status.done'), review: false };
  if (render?.status === 'error') return { text: t('cleaner.status.error'), review: false };
  return { text: t('cleaner.status.rendering'), review: false };
}

/**
 * Sección Limpiador (spec 013, D-6): elegir archivos, el modelo y los márgenes, y analizarlos. «Analizar» revisa cada
 * archivo; «Aplicar todos sin revisar» también renderiza. El lote muestra el estado de cada uno, y «Revisar» abre su revisión.
 */
export function CleanerPage(): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const [model] = useSetting<string>('select.whisper.model', 'large-v3-turbo');
  const [language] = useSetting<string>('select.cleaner.language', 'es');
  const [files, setFiles] = useState<string[]>([]);
  const [minGap, setMinGap] = useState(500);
  const [padding, setPadding] = useState(150);
  const [edges, setEdges] = useState(true);
  const [review, setReview] = useState<number | null>(null);
  const analyses = useQuery({
    queryKey: ['jobs', 'clean.analyze'],
    queryFn: () => api.get<Job[]>('/jobs?kind=clean.analyze'),
    refetchInterval: 2000,
  });
  const renders = useQuery({
    queryKey: ['jobs', 'clean.render'],
    queryFn: () => api.get<Job[]>('/jobs?kind=clean.render'),
    refetchInterval: 2000,
  });

  const submit = useMutation({
    mutationFn: (autoRender: boolean) =>
      Promise.all(
        files.map((input) =>
          api.post<Job>('/jobs', {
            kind: 'clean.analyze',
            params: {
              input,
              model,
              language,
              min_gap: minGap / 1000,
              padding: padding / 1000,
              edges,
              auto_render: autoRender,
            },
          }),
        ),
      ),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });

  async function pick() {
    const chosen = await open({
      multiple: true,
      filters: [{ name: t('cleaner.files.filter'), extensions: MEDIA_EXTENSIONS }],
    });
    if (chosen === null) return;
    const list = Array.isArray(chosen) ? chosen : [chosen];
    setFiles((current) => [...new Set([...current, ...list])]);
  }

  if (review !== null) {
    return <CleanReview jobId={review} onBack={() => setReview(null)} />;
  }

  const rendered = renders.data ?? [];

  return (
    <UIStack gap="lg">
      <UIWhisperModelSelect />
      <UIRecommendedSelect settingKey="select.cleaner.language" label={t('cleaner.options.language')} options={languageOptions()} />
      <UIStack direction="row" align="end" gap="sm">
        <UIField
          type="number"
          min={0}
          label={t('cleaner.options.min_gap')}
          value={minGap}
          onChange={(event) => setMinGap(number(event.target.value))}
        />
        <UIField
          type="number"
          min={0}
          label={t('cleaner.options.padding')}
          value={padding}
          onChange={(event) => setPadding(number(event.target.value))}
        />
        <UISwitch label={t('cleaner.options.edges')} checked={edges} onChange={setEdges} />
      </UIStack>
      <UIButton variant="secondary" className="self-start" onClick={() => void pick()}>
        {t('cleaner.files.pick')}
      </UIButton>
      {files.length === 0 ? (
        <UIText variant="caption">{t('cleaner.files.empty')}</UIText>
      ) : (
        <UIStack gap="xs">
          {files.map((file) => (
            <UIText key={file} variant="body">
              {baseName(file)}
            </UIText>
          ))}
        </UIStack>
      )}
      <UIStack direction="row" gap="sm">
        <UIButton disabled={files.length === 0 || submit.isPending} onClick={() => submit.mutate(false)}>
          {t('cleaner.analyze')}
        </UIButton>
        <UIButton variant="secondary" disabled={files.length === 0 || submit.isPending} onClick={() => submit.mutate(true)}>
          {t('cleaner.auto')}
        </UIButton>
      </UIStack>
      <UIText variant="subtitle">{t('cleaner.batch.title')}</UIText>
      {(analyses.data ?? []).length === 0 ? (
        <UIText variant="caption">{t('cleaner.batch.empty')}</UIText>
      ) : (
        (analyses.data ?? []).map((job) => {
          const state = statusOf(job, rendered);
          const input = (job.params as { input?: string }).input ?? '';
          return (
            <UIStack key={job.id} direction="row" align="center" gap="sm">
              <UIText variant="body">{baseName(input)}</UIText>
              <UIText variant="caption">{state.text}</UIText>
              {state.review ? (
                <UIButton variant="secondary" onClick={() => setReview(job.id)}>
                  {t('cleaner.review')}
                </UIButton>
              ) : null}
            </UIStack>
          );
        })
      )}
    </UIStack>
  );
}
