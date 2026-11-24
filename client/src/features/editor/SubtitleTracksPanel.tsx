import { useEffect, useState } from 'react';

import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIProgress } from '@/shared/components/atoms/UIProgress';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { t } from '@/shared/i18n/t';

import type { Doc, SubtitleTrack } from './model/types';

type ProjectRow = { id: number; name: string };
type Job = { id: number; status: string; progress: number; result: unknown };

function subtitleTrack(project: ProjectRow): SubtitleTrack {
  return {
    id: crypto.randomUUID(),
    kind: 'subtitles',
    name: project.name,
    subtitles_project: String(project.id),
    locked: false,
    height: 48,
  };
}

async function waitForJob(
  getJob: (id: number) => Promise<Job>,
  id: number,
  update: (job: Job) => void,
): Promise<Job> {
  while (true) {
    const job = await getJob(id);
    update(job);
    if (job.status === 'done') return job;
    if (job.status === 'error' || job.status === 'cancelled') throw new Error(job.status);
    await new Promise((resolve) => window.setTimeout(resolve, 1000));
  }
}

/** Selección de proyectos 014 o transcripción en cola de la mezcla de audio del editor. */
export function SubtitleTracksPanel({
  doc,
  path,
  onAdd,
}: {
  doc: Doc;
  path: string;
  onAdd: (track: SubtitleTrack) => void;
}): React.JSX.Element {
  const api = useApi();
  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [selected, setSelected] = useState('');
  const [activeJob, setActiveJob] = useState<Job | null>(null);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    void api.get<ProjectRow[]>('/subtitles').then((rows) => {
      if (active) setProjects(rows);
    }).catch(() => {
      if (active) setError(true);
    });
    return () => {
      active = false;
    };
  }, [api]);

  function addProject(project: ProjectRow): void {
    onAdd(subtitleTrack(project));
  }

  async function transcribeMix(): Promise<void> {
    setWorking(true);
    setError(false);
    try {
      const render = await api.post<Job>('/jobs', {
        kind: 'editor.render',
        params: { doc: path, format: 'wav', name: 'editor-subtitles-mix' },
      });
      const completedRender = await waitForJob((id) => api.get<Job>(`/jobs/${id}`), render.id, setActiveJob);
      const mixPath = (completedRender.result as { output?: string } | null)?.output;
      if (!mixPath) throw new Error('missing_mix');
      const transcript = await api.post<Job>('/jobs', {
        kind: 'transcribe',
        params: { input: mixPath, model: 'large-v3-turbo', language: 'auto' },
      });
      setActiveJob(transcript);
      const completedTranscript = await waitForJob((id) => api.get<Job>(`/jobs/${id}`), transcript.id, setActiveJob);
      const project = await api.post<ProjectRow>('/subtitles/from-transcript', { job_id: completedTranscript.id });
      setProjects((current) => [project, ...current]);
      setSelected(String(project.id));
      addProject(project);
    } catch {
      setError(true);
    } finally {
      setWorking(false);
      setActiveJob(null);
    }
  }

  const selectedProject = projects.find((project) => String(project.id) === selected);
  const hasAudio = doc.clips.some((clip) => clip.media === undefined);

  return (
    <UIStack gap="xs">
      <UISelect
        label={t('editor.subtitles.project')}
        value={selected}
        emptyOption={t('editor.subtitles.empty')}
        options={projects.map((project) => ({ value: String(project.id), label: project.name }))}
        onChange={setSelected}
      />
      <UIStack direction="row" gap="xs">
        <UIButton variant="secondary" disabled={!selectedProject || working} onClick={() => selectedProject && addProject(selectedProject)}>
          {t('editor.subtitles.add')}
        </UIButton>
        {selectedProject ? (
          <UIButton
            variant="secondary"
            disabled={working}
            onClick={() => { window.location.hash = `#/subtitles?project=${selectedProject.id}`; }}
          >
            {t('editor.subtitles.edit')}
          </UIButton>
        ) : null}
      </UIStack>
      <UIButton variant="secondary" disabled={!hasAudio || working} loading={working} onClick={() => void transcribeMix()}>
        {working ? t('editor.subtitles.working') : t('editor.subtitles.transcribe')}
      </UIButton>
      {activeJob ? <UIProgress value={activeJob.progress} label={t('editor.subtitles.working')} /> : null}
      {error ? <UIText variant="caption">{t('editor.subtitles.error')}</UIText> : null}
    </UIStack>
  );
}
