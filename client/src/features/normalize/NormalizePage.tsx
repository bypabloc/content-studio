import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { openPath } from '@tauri-apps/plugin-opener';
import { useState } from 'react';

import { useApi } from '@/shared/api/context';
import type { Job } from '@/shared/api/events';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIProgress } from '@/shared/components/atoms/UIProgress';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UISwitch } from '@/shared/components/atoms/UISwitch';
import { UIAlert } from '@/shared/components/molecules/UIAlert';
import { UIField } from '@/shared/components/molecules/UIField';
import { type SelectOption, UIRecommendedSelect } from '@/shared/components/molecules/UIRecommendedSelect';
import { toast } from '@/shared/components/molecules/UIToast';
import { UIDropZone } from '@/shared/components/organisms/UIDropZone';
import { UIErrorDetailDialog } from '@/shared/components/organisms/UIErrorDetailDialog';
import { UITable, type UITableColumn } from '@/shared/components/organisms/UITable';
import { useFilePaths } from '@/shared/hooks/useFilePaths';
import { useRecommendedValue } from '@/shared/hooks/useRecommendedValue';
import { useSetting } from '@/shared/hooks/useSetting';
import { type MessageKey, t } from '@/shared/i18n/t';
import { MEDIA_EXTENSIONS, baseName, isVideoPath, jobErrorMessage } from '@/shared/media/formats';

import { NormalizeListen } from './NormalizeListen';

/** Lo que mide `ebur128` de un archivo: sonoridad integrada (LUFS), pico real (dBTP) y rango de sonoridad (LU). */
interface Measures {
  I: number;
  TP: number;
  LRA: number;
}

/** Lo que escribe el servicio en `result.json` de la carpeta del trabajo. */
interface Report {
  before: Measures;
  after: Measures;
  mode: string;
  target: number;
}

const PRESETS = ['youtube', 'podcast', 'broadcast', 'custom'];

/** Los presets de sonoridad: ★ `podcast` si todos son audio hablado, y `youtube` si hay video. */
function presetOptions(allAudio: boolean): SelectOption[] {
  const recommended = allAudio ? 'podcast' : 'youtube';
  return PRESETS.map((preset) => ({
    value: preset,
    label: t(`normalize.preset.${preset}` as MessageKey),
    recommended: preset === recommended,
  }));
}

/** Una medida (I, TP o LRA) de un archivo, con su unidad; `—` si el trabajo todavía no la tiene. */
function MeasureCells({ job, side }: { job: Job; side: 'before' | 'after' }): React.JSX.Element {
  const api = useApi();
  const report = useQuery({
    queryKey: ['normalize-report', job.id],
    queryFn: () => api.get<Report>(`/files?path=${encodeURIComponent(`${job.output_dir ?? ''}/result.json`)}`),
    enabled: job.status === 'done' && job.output_dir !== null,
  });
  const measures = report.data?.[side];
  if (!measures) return <UIText variant="caption">{t('normalize.measure.none')}</UIText>;
  return (
    <UIStack direction="row" gap="sm" align="center">
      <UIText variant="body">{measures.I.toFixed(1)}</UIText>
      <UIText variant="caption">{t('normalize.measure.I')}</UIText>
      <UIText variant="body">{measures.TP.toFixed(1)}</UIText>
      <UIText variant="caption">{t('normalize.measure.TP')}</UIText>
      <UIText variant="body">{measures.LRA.toFixed(1)}</UIText>
      <UIText variant="caption">{t('normalize.measure.LRA')}</UIText>
    </UIStack>
  );
}

/**
 * Normalizar (spec 015, D-4 y D-6): un lote de archivos con un preset de sonoridad ★, «Mejorar voz» opcional, la
 * tabla con la sonoridad antes y después de cada uno, y un A/B para escuchar el original y el resultado.
 *
 * @author Pablo Contreras
 * @since 2026/11/22
 */
export function NormalizePage(): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const [files, setFiles] = useState<string[]>([]);
  const [failed, setFailed] = useState<Job | null>(null);
  const [listening, setListening] = useState<Job | null>(null);
  const [customTarget, setCustomTarget] = useState(-16);
  const [enhance, setEnhance] = useSetting<boolean>('select.normalize.enhance', false);

  const presets = presetOptions(files.every((file) => !isVideoPath(file)));
  const [preset] = useRecommendedValue('select.normalize.preset', presets);
  const jobs = useQuery({
    queryKey: ['jobs', 'media.normalize'],
    queryFn: () => api.get<Job[]>('/jobs?kind=media.normalize'),
    refetchInterval: 2000,
  });

  const { dragging, pick } = useFilePaths({
    extensions: MEDIA_EXTENSIONS,
    onPaths: (paths) => setFiles((current) => [...new Set([...current, ...paths])]),
    onRejected: (paths) => toast.error(t('media.files.rejected', { names: paths.map(baseName).join(', ') })),
  });

  const submit = useMutation({
    mutationFn: () =>
      Promise.all(
        files.map((input) =>
          api.post<Job>('/jobs', {
            kind: 'media.normalize',
            params: { input, preset, enhance, ...(preset === 'custom' ? { target: customTarget } : {}) },
          }),
        ),
      ),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });
  const retry = useMutation({
    mutationFn: (id: number) => api.post(`/jobs/${id}/retry`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });

  const columns: UITableColumn<Job>[] = [
    { key: 'file', header: t('media.batch.file'), render: (job) => baseName((job.params as { input: string }).input) },
    {
      key: 'state',
      header: t('media.batch.state'),
      render: (job) => (
        <UIStack gap="xs">
          <UIText variant="body">{job.status === 'done' ? t('media.status.done') : job.status === 'error' ? t('media.status.error') : t('media.status.running', { percent: Math.round(job.progress * 100) })}</UIText>
          {job.status === 'running' ? <UIProgress value={job.progress} label={baseName((job.params as { input: string }).input)} /> : null}
        </UIStack>
      ),
    },
    { key: 'before', header: t('normalize.column.before'), wide: true, render: (job) => <MeasureCells job={job} side="before" /> },
    { key: 'after', header: t('normalize.column.after'), wide: true, render: (job) => <MeasureCells job={job} side="after" /> },
    {
      key: 'actions',
      header: t('media.batch.actions'),
      align: 'end',
      render: (job) => (
        <UIStack direction="row" gap="xs" justify="end">
          {job.status === 'done' ? (
            <>
              <UIButton variant="secondary" onClick={() => setListening(job)}>
                {t('media.action.listen')}
              </UIButton>
              <UIButton variant="secondary" onClick={() => void openPath(job.output_dir ?? '')}>
                {t('media.action.folder')}
              </UIButton>
            </>
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
        </UIStack>
      ),
    },
  ];

  return (
    <UIStack gap="lg">
      <UIDropZone
        dragging={dragging}
        title={t('media.files.drop')}
        hint={t('normalize.files.hint')}
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
      <UIRecommendedSelect settingKey="select.normalize.preset" label={t('normalize.preset.label')} options={presets} />
      {preset === 'custom' ? (
        <UIField type="number" label={t('normalize.custom.target')} value={customTarget} onChange={(event) => setCustomTarget(Number(event.target.value))} />
      ) : null}
      <UISwitch label={t('normalize.enhance')} checked={enhance} onChange={setEnhance} />
      <UIButton disabled={files.length === 0 || submit.isPending} onClick={() => submit.mutate()} className="self-start">
        {t('normalize.submit')}
      </UIButton>
      {submit.error ? <UIAlert>{submit.error.message}</UIAlert> : null}
      <UITable
        caption={t('media.batch.title')}
        columns={columns}
        rows={jobs.data ?? []}
        rowKey={(job) => job.id}
        empty={<UIText variant="caption">{t('media.batch.empty')}</UIText>}
      />
      {listening ? <NormalizeListen job={listening} /> : null}
      <UIErrorDetailDialog
        open={failed !== null}
        onOpenChange={(open) => {
          if (!open) setFailed(null);
        }}
        title={t('normalize.error.title')}
        message={jobErrorMessage(failed?.error_code)}
        detail={failed?.error_detail}
        closeLabel={t('media.dialog.close')}
      />
    </UIStack>
  );
}
