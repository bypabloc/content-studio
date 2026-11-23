import { useEffect, useRef, useState } from 'react';

import { openPath } from '@tauri-apps/plugin-opener';

import { useApi } from '@/shared/api/context';
import { UICheckbox } from '@/shared/components/atoms/UICheckbox';
import { UIMedia } from '@/shared/components/atoms/UIMedia';
import { UICard } from '@/shared/components/atoms/UICard';
import { UIProgress } from '@/shared/components/atoms/UIProgress';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIField } from '@/shared/components/molecules/UIField';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { t } from '@/shared/i18n/t';
import type { Marker } from './model/types';

type Job = { id: number; status: string; progress: number; error_code: string | null; error_detail: string | null };
type Normalize = '' | 'podcast' | 'youtube';
type Segment = { start?: number; end?: number; name: string };
type PlayMedia = { path: string; kind: 'audio' | 'video' };

const AUDIO_FORMATS = ['wav', 'mp3', 'flac', 'm4a', 'ogg-opus'].map((value) => ({ value, label: value.toUpperCase() }));
const VIDEO_FORMATS = [
  { value: 'mp4-h264', label: t('editor.export.format.mp4_recommended') },
  { value: 'webm-vp9', label: t('convert.format.webm-vp9') },
];
const NORMALIZATIONS = [
  { value: '', label: t('editor.export.normalize_none') },
  { value: 'podcast', label: t('editor.export.normalize_podcast') },
  { value: 'youtube', label: t('editor.export.normalize_youtube') },
];

function projectName(path: string): string {
  return path.split(/[\\/]/).filter(Boolean).at(-2) ?? 'export';
}

function exportsPath(path: string): string {
  const folder = path.replace(/[\\/][^\\/]+$/, '');
  const separator = path.includes('\\') ? '\\' : '/';
  return `${folder}${separator}exports`;
}

function parts(duration: number, markers: Marker[], name: string): Segment[] {
  const stops = [0, ...markers.map((marker) => marker.t), duration].filter((time, index, all) => time >= 0 && time <= duration && all.indexOf(time) === index).sort((a, b) => a - b);
  return stops.slice(0, -1).flatMap((start, index) => {
    const end = stops[index + 1];
    return end > start ? [{ start, end, name: `${name}-${String(index + 1).padStart(2, '0')}` }] : [];
  });
}

function missingSourcePaths(job: Job): string[] {
  if (job.error_code !== 'missing_source' || !job.error_detail) return [];
  try {
    const result = JSON.parse(job.error_detail) as { params?: { paths?: unknown } };
    return Array.isArray(result.params?.paths) ? result.params.paths.filter((path): path is string => typeof path === 'string') : [];
  } catch {
    return [];
  }
}

/** Encola el render, muestra el progreso y abre o reproduce la última salida. */
export function ExportDialog({ path, duration, markers }: { path: string; duration: number; markers: Marker[] }): React.JSX.Element {
  const api = useApi();
  const [open, setOpen] = useState(false);
  const [audioOnly, setAudioOnly] = useState(false);
  const [audioFormat, setAudioFormat] = useState('wav');
  const [videoFormat, setVideoFormat] = useState('mp4-h264');
  const [quality, setQuality] = useState(19);
  const [normalize, setNormalize] = useState<Normalize>('');
  const [name, setName] = useState(() => projectName(path));
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState(false);
  const [playMedia, setPlayMedia] = useState<PlayMedia | null>(null);
  const mediaRef = useRef<HTMLMediaElement | null>(null);
  const jobIds = jobs.map((job) => job.id);
  const format = audioOnly ? audioFormat : videoFormat;

  useEffect(() => {
    if (!jobIds.length) return;
    let active = true;
    let timer = 0;
    const refresh = async () => {
      try {
        const latest = await Promise.all(jobIds.map((id) => api.get<Job>(`/jobs/${id}`)));
        if (!active) return;
        setJobs(latest);
        if (latest.every((job) => job.status === 'done' || job.status === 'error' || job.status === 'cancelled')) {
          window.clearInterval(timer);
        }
      } catch {
        if (active) setError(true);
      }
    };
    void refresh();
    timer = window.setInterval(() => void refresh(), 1000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
    // Each poll uses the ids returned by the completed enqueue operation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api, jobIds.join(',')]);

  useEffect(() => {
    if (playMedia && mediaRef.current) {
      mediaRef.current.currentTime = 0;
      void mediaRef.current.play().catch(() => undefined);
    }
  }, [playMedia]);

  async function enqueue(segment: Segment): Promise<number> {
    const params = {
      doc: path,
      format,
      name: segment.name,
      normalize: normalize || null,
      ...(!audioOnly ? { quality } : {}),
      ...(segment.start === undefined ? {} : { start: segment.start, end: segment.end }),
    };
    const job = await api.post<Job>('/jobs', { kind: 'editor.render', params });
    return job.id;
  }

  async function start(segments: Segment[]): Promise<void> {
    setError(false);
    setJobs([]);
    try {
      const ids: number[] = [];
      for (const segment of segments) ids.push(await enqueue(segment));
      setJobs(ids.map((id) => ({ id, status: 'queued', progress: 0, error_code: null, error_detail: null })));
    } catch {
      setError(true);
    }
  }

  async function playLatest(): Promise<void> {
    try {
      const query = new URLSearchParams({ path: exportsPath(path), kinds: 'audio,video' });
      const result = await api.get<{ entries: Array<{ path: string; kind: string; modified: number }> }>(`/fs/list?${query}`);
      const latest = result.entries
        .filter((entry): entry is typeof entry & PlayMedia => entry.kind === 'audio' || entry.kind === 'video')
        .sort((a, b) => b.modified - a.modified)[0];
      setPlayMedia(latest ? { path: latest.path, kind: latest.kind } : null);
    } catch {
      setError(true);
    }
  }

  const completed = jobs.length > 0 && jobs.every((job) => job.status === 'done');
  const failed = jobs.some((job) => job.status === 'error');
  const missingSources = [...new Set(jobs.flatMap(missingSourcePaths))];
  const progress = jobs.length ? jobs.reduce((sum, job) => sum + job.progress, 0) / jobs.length : 0;

  return (
    <UIStack gap="sm">
      <UIButton variant="secondary" onClick={() => setOpen((current) => !current)}>
        {t('editor.export.open')}
      </UIButton>
      {open ? (
        <UICard role="dialog" aria-label={t('editor.export.dialog')}>
          <UIStack gap="sm">
            <UIField label={t('editor.export.name')} value={name} onChange={(event) => setName(event.target.value)} />
            <UICheckbox label={t('editor.export.audio_only')} checked={audioOnly} onChange={setAudioOnly} />
            <UISelect
              label={t('editor.export.format')}
              value={format}
              options={audioOnly ? AUDIO_FORMATS : VIDEO_FORMATS}
              onChange={(value) => (audioOnly ? setAudioFormat(value) : setVideoFormat(value))}
            />
            {!audioOnly ? (
              <UIField
                label={t('editor.export.quality')}
                type="number"
                min={0}
                max={51}
                step={1}
                value={quality}
                onChange={(event) => setQuality(Number(event.target.value))}
              />
            ) : null}
            <UISelect
              label={t('normalize.submit')}
              value={normalize}
              options={NORMALIZATIONS}
              onChange={(value) => setNormalize(value as Normalize)}
            />
            <UIStack direction="row" gap="sm">
              <UIButton onClick={() => void start([{ name: name || projectName(path) }])}>{t('editor.export.start')}</UIButton>
              {markers.length > 0 ? (
                <UIButton variant="secondary" onClick={() => void start(parts(duration, markers, name || projectName(path)))}>
                  {t('editor.export.markers')}
                </UIButton>
              ) : null}
            </UIStack>
            {jobs.length > 0 ? <UIProgress value={progress} label={t('editor.export.progress')} /> : null}
            {failed || error ? (
              <UIText variant="caption">
                {missingSources.length
                  ? t('editor.export.missing_source', { paths: missingSources.join(', ') })
                  : t('editor.export.failed')}
              </UIText>
            ) : null}
            {completed ? (
              <UIStack direction="row" gap="sm">
                <UIButton variant="secondary" onClick={() => void openPath(exportsPath(path))}>{t('media.action.folder')}</UIButton>
                <UIButton variant="secondary" onClick={() => void playLatest()}>{t('editor.export.play')}</UIButton>
              </UIStack>
            ) : null}
          </UIStack>
        </UICard>
      ) : null}
      {playMedia ? (
        <UIMedia kind={playMedia.kind} src={api.queryUrl('/fs/media', { path: playMedia.path })} mediaRef={(element) => (mediaRef.current = element)} />
      ) : null}
    </UIStack>
  );
}
