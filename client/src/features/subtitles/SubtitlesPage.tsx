import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { useState } from 'react';

import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UILink } from '@/shared/components/atoms/UILink';
import { UICard } from '@/shared/components/atoms/UICard';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UISwitch } from '@/shared/components/atoms/UISwitch';
import { UIText } from '@/shared/components/atoms/UIText';
import { toast } from '@/shared/components/molecules/UIToast';
import { UIEmpty } from '@/shared/components/molecules/UIEmpty';
import { UIField } from '@/shared/components/molecules/UIField';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { UIWhisperModelSelect } from '@/shared/components/molecules/UIWhisperModelSelect';
import { textParam, useFromJob } from '@/shared/hooks/useFromJob';
import { useRecommendedValue } from '@/shared/hooks/useRecommendedValue';
import { useSetting } from '@/shared/hooks/useSetting';
import { type MessageKey, t } from '@/shared/i18n/t';
import { hashParams } from '@/shared/navigation/hash';

import { SubtitlesEditor } from './SubtitlesEditor';

interface ProjectRow {
  id: number;
  name: string;
  source_path: string;
  updated_at: string;
}

type Origin = 'file' | 'cleaner' | 'narration' | 'import';

const ORIGINS: Origin[] = ['file', 'cleaner', 'narration', 'import'];
type EngineInfo = components['schemas']['EngineInfo'];

/** Los idiomas de Subtítulos: los mismos que la Transcripción; «auto» deja que el modelo detecte el idioma. */
const LANGUAGES = ['auto', 'es', 'en', 'pt', 'fr', 'de', 'it'] as const;
const MEDIA = ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac', 'mp4', 'mov', 'mkv', 'webm', 'avi', 'm4v', 'srt', 'vtt'];

function requestedProject(): number | null {
  const query = window.location.hash.split('?')[1] ?? '';
  const project = Number(new URLSearchParams(query).get('project'));
  return Number.isSafeInteger(project) && project > 0 ? project : null;
}

/**
 * La sección Subtítulos (D-9): los proyectos guardados y «Nuevo», que encola `subtitles.create` con su origen. Abrir un
 * proyecto muestra su editor.
 */
export function SubtitlesPage(): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const [openId, setOpenId] = useState<number | null>(requestedProject);
  const [origin, setOrigin] = useState<Origin>('file');
  const originLabels: Record<Origin, string> = {
    file: t('subtitles.origin.file'),
    cleaner: t('subtitles.origin.cleaner'),
    narration: t('subtitles.origin.narration'),
    import: t('subtitles.origin.import'),
  };
  const [input, setInput] = useState(() => hashParams().get('path') ?? '');
  // «Editar y repetir» (spec 020): el archivo de origen del trabajo, una vez.
  const source = useFromJob();
  const [appliedJob, setAppliedJob] = useState<number | null>(null);
  if (source !== null && source.id !== appliedJob) {
    setAppliedJob(source.id);
    setInput(textParam(source, 'input', input));
  }
  const projects = useQuery({ queryKey: ['subtitles'], queryFn: () => api.get<ProjectRow[]>('/subtitles') });
  // El modelo, el idioma y los hablantes son los de la Transcripción (mismas claves de ajuste y de motor).
  const engines = useQuery({ queryKey: ['engines'], queryFn: () => api.get<EngineInfo[]>('/engines') });
  const whisper = engines.data?.find((engine) => engine.engine === 'faster-whisper');
  const modelOptions = (whisper?.models ?? []).map((model) => ({ value: model.model, label: model.model, recommended: model.recommended }));
  const [model] = useRecommendedValue('select.whisper.model', modelOptions);
  const [language, setLanguage] = useSetting<string>('select.transcription.language', 'auto');
  const speakersAvailable = engines.data?.find((engine) => engine.engine === 'pyannote')?.status === 'installed';
  const [speakers, setSpeakers] = useState(false);
  const create = useMutation({
    mutationFn: () =>
      api.post('/jobs', {
        kind: 'subtitles.create',
        params: { origin, input, model, language, ...(speakers && speakersAvailable ? { diarize: true } : {}) },
      }),
    onSuccess: () => {
      setInput('');
      void queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    // El server rechaza el trabajo (p. ej. un .txt al importar) con su código: el aviso lleva el texto del catálogo.
    onError: (error: Error) => toast.error(error.message),
  });

  async function pick() {
    const chosen = await open({ multiple: false, filters: [{ name: t('subtitles.home.input'), extensions: MEDIA }] });
    if (typeof chosen === 'string') setInput(chosen);
  }

  if (openId !== null) {
    return (
      <UIStack gap="md">
        <UIButton variant="secondary" onClick={() => setOpenId(null)}>
          {t('subtitles.home.back')}
        </UIButton>
        <SubtitlesEditor projectId={openId} />
      </UIStack>
    );
  }

  return (
    <UIStack gap="lg">
      <UICard>
        <UIStack gap="md">
          <UIText variant="subtitle">{t('subtitles.home.new')}</UIText>
          <UISelect
            label={t('subtitles.home.origin')}
            value={origin}
            options={ORIGINS.map((value) => ({ value, label: originLabels[value] }))}
            onChange={(value) => setOrigin(value as Origin)}
          />
          <UIField label={t('subtitles.home.input')} value={input} onChange={(event) => setInput(event.target.value)} />
          <UIWhisperModelSelect />
          <UISelect
            label={t('transcription.language')}
            value={language}
            options={LANGUAGES.map((code) => ({ value: code, label: t(`cleaner.language.${code}` as MessageKey) }))}
            onChange={(value) => setLanguage(value)}
          />
          <UISwitch
            label={t('subtitles.home.diarize')}
            description={speakersAvailable ? undefined : t('transcription.diarize.missing')}
            checked={speakers && speakersAvailable}
            disabled={!speakersAvailable}
            onChange={setSpeakers}
          />
          {!speakersAvailable ? (
            <UILink href="#/engines" variant="inline" className="underline">
              {t('transcription.diarize.engines')}
            </UILink>
          ) : null}
          <UIStack direction="row" gap="sm">
            <UIButton variant="secondary" onClick={() => void pick()}>
              {t('subtitles.home.pick')}
            </UIButton>
            <UIButton disabled={!input} onClick={() => create.mutate()}>
              {t('subtitles.home.create')}
            </UIButton>
          </UIStack>
        </UIStack>
      </UICard>
      <UIStack gap="sm">
        <UIText variant="subtitle">{t('subtitles.home.projects')}</UIText>
        {(projects.data ?? []).length === 0 ? (
          <UIEmpty icon="narration" title={t('subtitles.home.empty')} />
        ) : (
          (projects.data ?? []).map((project) => (
            <UICard key={project.id}>
              <UIStack direction="row" gap="sm" align="center">
                <UIText variant="body">{project.name}</UIText>
                <UIButton variant="secondary" onClick={() => setOpenId(project.id)}>
                  {t('subtitles.home.open')}
                </UIButton>
              </UIStack>
            </UICard>
          ))
        )}
      </UIStack>
    </UIStack>
  );
}
