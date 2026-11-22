import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { useState } from 'react';

import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICard } from '@/shared/components/atoms/UICard';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIEmpty } from '@/shared/components/molecules/UIEmpty';
import { UIField } from '@/shared/components/molecules/UIField';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { t } from '@/shared/i18n/t';

import { SubtitlesEditor } from './SubtitlesEditor';

interface ProjectRow {
  id: number;
  name: string;
  source_path: string;
  updated_at: string;
}

type Origin = 'file' | 'cleaner' | 'narration' | 'import';

const ORIGINS: Origin[] = ['file', 'cleaner', 'narration', 'import'];
const MEDIA = ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac', 'mp4', 'mov', 'mkv', 'webm', 'avi', 'm4v', 'srt', 'vtt'];

/**
 * La sección Subtítulos (D-9): los proyectos guardados y «Nuevo», que encola `subtitles.create` con su origen. Abrir un
 * proyecto muestra su editor.
 */
export function SubtitlesPage(): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const [openId, setOpenId] = useState<number | null>(null);
  const [origin, setOrigin] = useState<Origin>('file');
  const originLabels: Record<Origin, string> = {
    file: t('subtitles.origin.file'),
    cleaner: t('subtitles.origin.cleaner'),
    narration: t('subtitles.origin.narration'),
    import: t('subtitles.origin.import'),
  };
  const [input, setInput] = useState('');
  const projects = useQuery({ queryKey: ['subtitles'], queryFn: () => api.get<ProjectRow[]>('/subtitles') });
  const create = useMutation({
    mutationFn: () => api.post('/jobs', { kind: 'subtitles.create', params: { origin, input } }),
    onSuccess: () => {
      setInput('');
      void queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
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
