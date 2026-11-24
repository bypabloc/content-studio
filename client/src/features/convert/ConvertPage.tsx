import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { openPath } from '@tauri-apps/plugin-opener';
import { useState } from 'react';

import { useApi } from '@/shared/api/context';
import type { Job } from '@/shared/api/events';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIProgress } from '@/shared/components/atoms/UIProgress';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIAlert } from '@/shared/components/molecules/UIAlert';
import { toast } from '@/shared/components/molecules/UIToast';
import { UIDropZone } from '@/shared/components/organisms/UIDropZone';
import { UIErrorDetailDialog } from '@/shared/components/organisms/UIErrorDetailDialog';
import { UITable, type UITableColumn } from '@/shared/components/organisms/UITable';
import { useFilePaths } from '@/shared/hooks/useFilePaths';
import { t } from '@/shared/i18n/t';
import { MEDIA_EXTENSIONS, baseName, isVideoPath, jobErrorMessage } from '@/shared/media/formats';
import { OpenJobOutputButton } from '@/shared/navigation/OpenJobOutputButton';
import { textParam, useFromJob } from '@/shared/hooks/useFromJob';
import { hashParams } from '@/shared/navigation/hash';

import { FormatPicker } from './FormatPicker';
import { type Catalog, type FormatChoice, type Reframe, SOCIAL, convertJob } from './convertOptions';
import { ReframePreview } from './ReframePreview';

type MediaInfo = { width: number | null; height: number | null };

/** El texto de un estado: en cola, convirtiendo con su porcentaje, listo, con error o cancelado. */
function statusText(job: Job): string {
  if (job.status === 'running') return t('media.status.running', { percent: Math.round(job.progress * 100) });
  if (job.status === 'queued') return t('media.status.queued');
  if (job.status === 'done') return t('media.status.done');
  if (job.status === 'cancelled') return t('media.status.cancelled');
  return t('media.status.error');
}

/**
 * Convertir (spec 015, D-6): se sueltan o eligen los archivos, se elige el formato, la calidad y, para Redes, el
 * encuadre. Cada archivo es un trabajo `media.convert` en la cola (en paralelo, hasta el pool), y la tabla muestra su
 * progreso, su error (con el detalle técnico) y sus acciones.
 *
 * @author Pablo Contreras
 * @since 2026/11/22
 */
export function ConvertPage(): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const [files, setFiles] = useState<string[]>(() => hashParams().getAll('path').filter(Boolean));
  // «Editar y repetir» (spec 020): el archivo de origen del trabajo, una vez; el formato se vuelve a elegir.
  const source = useFromJob();
  const [appliedJob, setAppliedJob] = useState<number | null>(null);
  if (source !== null && source.id !== appliedJob) {
    setAppliedJob(source.id);
    const input = textParam(source, 'input');
    if (input) setFiles([input]);
  }
  const [choice, setChoice] = useState<FormatChoice | null>(null);
  const [reframe, setReframe] = useState<Reframe | null>(null);
  const [failed, setFailed] = useState<Job | null>(null);

  const videoFile = files.find(isVideoPath);
  const info = useQuery({
    queryKey: ['media-info', videoFile],
    queryFn: () => api.get<MediaInfo>(`/media/info?path=${encodeURIComponent(videoFile ?? '')}`),
    enabled: videoFile !== undefined,
  });
  const width = info.data?.width ?? 1920;
  const height = info.data?.height ?? 1080;
  const catalog = useQuery({
    queryKey: ['catalog', 'media', width / height],
    queryFn: () => api.get<Catalog>(`/catalog/media?aspect=${width / height}`),
  });
  const jobs = useQuery({
    queryKey: ['jobs', 'media.convert'],
    queryFn: () => api.get<Job[]>('/jobs?kind=media.convert'),
    refetchInterval: 2000,
  });

  const { dragging, pick } = useFilePaths({
    extensions: MEDIA_EXTENSIONS,
    onPaths: (paths) => setFiles((current) => [...new Set([...current, ...paths])]),
    onRejected: (paths) => toast.error(t('media.files.rejected', { names: paths.map(baseName).join(', ') })),
  });

  const kind = files.some(isVideoPath) ? 'video' : 'audio';
  const preset = catalog.data?.presets.find((item) => item.id === choice?.preset);
  const social = choice?.format === SOCIAL;
  const submit = useMutation({
    mutationFn: () => Promise.all(files.map((input) => api.post<Job>('/jobs', convertJob(input, choice!, reframe, catalog.data!)))),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });
  const cancel = useMutation({
    mutationFn: (id: number) => api.post(`/jobs/${id}/cancel`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });
  const retry = useMutation({
    mutationFn: (id: number) => api.post(`/jobs/${id}/retry`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });

  const ready = files.length > 0 && choice !== null && catalog.data !== undefined && (!social || reframe !== null);

  const columns: UITableColumn<Job>[] = [
    { key: 'file', header: t('media.batch.file'), render: (job) => baseName((job.params as { input: string }).input) },
    {
      key: 'state',
      header: t('media.batch.state'),
      wide: true,
      render: (job) => (
        <UIStack gap="xs">
          <UIText variant="body">{statusText(job)}</UIText>
          {job.status === 'running' ? (
            <UIProgress value={job.progress} label={baseName((job.params as { input: string }).input)} />
          ) : null}
        </UIStack>
      ),
    },
    {
      key: 'actions',
      header: t('media.batch.actions'),
      align: 'end',
      render: (job) => (
        <UIStack direction="row" gap="xs" justify="end">
          {job.status === 'queued' || job.status === 'running' ? (
            <UIButton variant="secondary" onClick={() => cancel.mutate(job.id)}>
              {t('media.action.cancel')}
            </UIButton>
          ) : null}
          {job.status === 'error' ? (
            <>
              <UIButton variant="secondary" onClick={() => setFailed(job)}>
                {t('media.action.open_error')}
              </UIButton>
              <UIButton variant="secondary" onClick={() => retry.mutate(job.id)}>
                {t('media.action.retry')}
              </UIButton>
            </>
          ) : null}
          {job.status === 'done' && job.output_dir ? (
            <>
              <OpenJobOutputButton outputDir={job.output_dir} />
              <UIButton variant="secondary" onClick={() => void openPath(job.output_dir ?? '')}>
                {t('media.action.folder')}
              </UIButton>
            </>
          ) : null}
        </UIStack>
      ),
    },
  ];

  return (
    <UIStack gap="lg">
      <UIDropZone
        dragging={dragging}
        title={t('media.files.drop')}
        hint={t('convert.files.hint')}
        actionLabel={t('media.files.pick')}
        onPick={() => void pick()}
      />
      {files.length === 0 ? (
        <UIText variant="caption">{t('media.files.empty')}</UIText>
      ) : (
        <UIStack gap="xs">
          {files.map((file) => (
            <UIText key={file} variant="body">
              {baseName(file)}
            </UIText>
          ))}
        </UIStack>
      )}
      {catalog.data ? <FormatPicker kind={kind} catalog={catalog.data} onChange={setChoice} /> : null}
      {social && preset && videoFile ? (
        <ReframePreview
          source={{ path: videoFile, width, height }}
          target={{ width: preset.width, height: preset.height }}
          onChange={setReframe}
        />
      ) : null}
      <UIButton disabled={!ready || submit.isPending} onClick={() => submit.mutate()} className="self-start">
        {t('convert.submit')}
      </UIButton>
      {submit.error ? <UIAlert>{submit.error.message}</UIAlert> : null}
      <UITable
        caption={t('media.batch.title')}
        columns={columns}
        rows={jobs.data ?? []}
        rowKey={(job) => job.id}
        empty={<UIText variant="caption">{t('media.batch.empty')}</UIText>}
      />
      <UIErrorDetailDialog
        open={failed !== null}
        onOpenChange={(open) => {
          if (!open) setFailed(null);
        }}
        title={t('convert.error.title')}
        message={jobErrorMessage(failed?.error_code)}
        detail={failed?.error_detail}
        closeLabel={t('media.dialog.close')}
      />
    </UIStack>
  );
}
