import { useMutation, useQuery } from '@tanstack/react-query';

import { AssistantButton } from '@/features/assistant/AssistantButton';
import { useAssistantStatus, useAssistantTask } from '@/features/assistant/useAssistant';
import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIRecommendedSelect } from '@/shared/components/molecules/UIRecommendedSelect';
import { UITextarea } from '@/shared/components/molecules/UITextarea';
import { UITextDiff } from '@/shared/components/molecules/UITextDiff';
import { toast } from '@/shared/components/molecules/UIToast';
import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';

import { CueSuggestions } from './CueSuggestions';
import type { DocEdit } from './cues';

type Language = components['schemas']['Language'];
interface Translation {
  language: string;
  cues: { id: number; text: string; original: string; flag: string | null }[];
}
interface Correction {
  cues: { id: number; original: string; text: string; review: boolean }[];
}
interface Keywords {
  cues: { id: number; word: string; emoji: string | null }[];
}

interface Props {
  projectId: number;
  /** Guarda lo que el editor aún no guardó: la tarea lee el documento del disco. */
  onBeforeRun: () => Promise<void>;
  onApplied: (doc: DocEdit) => void;
}

/** Traducir, corregir con el glosario y sugerir palabras clave (spec 021, D-5). Nada cambia hasta aplicarlo. */
export function AssistantTools({ projectId, onBeforeRun, onApplied }: Props): React.JSX.Element | null {
  const api = useApi();
  const status = useAssistantStatus();
  const languages = useQuery({ queryKey: ['llm', 'languages'], queryFn: () => api.get<Language[]>('/llm/languages') });
  const [language] = useSetting('select.llm.language', 'en');
  const [glossary, setGlossary] = useSetting<string[]>('subtitles.glossary', []);
  const translate = useAssistantTask<Translation>('llm.subtitles_translate');
  const correct = useAssistantTask<Correction>('llm.subtitles_correct');
  const keywords = useAssistantTask<Keywords>('llm.subtitles_keywords');
  const apply = useMutation({
    mutationFn: ({ jobId, accepted }: { jobId: number; accepted: number[] | null }) =>
      api.post<DocEdit>(`/llm/subtitles/${projectId}/apply`, { job_id: jobId, accepted }),
    onSuccess: (doc) => {
      onApplied(doc);
      toast.success(t('llm.subtitles.applied'));
    },
    onError: (error: Error) => toast.error(error.message),
  });
  const run = async (task: { run: (params: Record<string, unknown>) => void }, params: Record<string, unknown>) => {
    await onBeforeRun();
    task.run({ project_id: projectId, ...params });
  };
  const applyFor = (task: { jobId: number | null; reset: () => void }) => (accepted: number[] | null) => {
    if (task.jobId !== null) apply.mutate({ jobId: task.jobId, accepted }, { onSuccess: task.reset });
  };

  if (!status.data?.enabled) return null;
  const options = Array.isArray(languages.data) ? languages.data : [];
  return (
    <UIStack role="region" aria-label={t('llm.subtitles.title')} gap="md">
      <UIText variant="subtitle">{t('llm.subtitles.title')}</UIText>
      <UIRecommendedSelect
        settingKey="select.llm.language"
        label={t('llm.subtitles.language')}
        options={options.map((item) => ({ value: item.code, label: item.name, recommended: item.recommended }))}
      />
      <AssistantButton label={t('llm.button.translate')} busy={translate.busy} error={translate.error} onClick={() => void run(translate, { language })} />
      {translate.result ? (
        <CueSuggestions
          key={translate.jobId}
          title={t('llm.button.translate')}
          selectable={false}
          busy={apply.isPending}
          rows={translate.result.cues.map((cue) => ({
            id: cue.id,
            content: (
              <UIStack gap="xs">
                <UIText variant="caption">{cue.original}</UIText>
                <UIText variant="body">{cue.text}</UIText>
              </UIStack>
            ),
            flag: cue.flag,
          }))}
          onApply={applyFor(translate)}
        />
      ) : null}
      <UITextarea
        label={t('llm.subtitles.glossary')}
        value={glossary.join('\n')}
        onChange={(event) => setGlossary(event.target.value.split('\n'))}
        className="min-h-20"
      />
      <AssistantButton
        label={t('llm.button.correct')}
        busy={correct.busy}
        error={correct.error}
        onClick={() => void run(correct, { glossary: glossary.map((term) => term.trim()).filter(Boolean) })}
      />
      {correct.result ? (
        <CueSuggestions
          key={correct.jobId}
          title={t('llm.button.correct')}
          busy={apply.isPending}
          rows={correct.result.cues.map((cue) => ({
            id: cue.id,
            content: <UITextDiff before={cue.original} after={cue.text} />,
            flag: cue.review ? 'review' : null,
            checked: !cue.review,
          }))}
          onApply={applyFor(correct)}
        />
      ) : null}
      <AssistantButton label={t('llm.button.keywords')} busy={keywords.busy} error={keywords.error} onClick={() => void run(keywords, {})} />
      {keywords.result ? (
        <CueSuggestions
          key={keywords.jobId}
          title={t('llm.button.keywords')}
          busy={apply.isPending}
          rows={keywords.result.cues.map((cue) => ({ id: cue.id, content: <UIText variant="body">{`${cue.word} ${cue.emoji ?? ''}`}</UIText> }))}
          onApply={applyFor(keywords)}
        />
      ) : null}
    </UIStack>
  );
}
