import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { toast } from '@/shared/components/molecules/UIToast';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { t } from '@/shared/i18n/t';

import { MixTimeline } from './MixTimeline';
import { useMixPreview } from './useMixPreview';
import type { MixParams, MixProject } from './types';

interface CurveOut {
  total: number;
  points: [number, number][];
}

const DUCK_OPTIONS = ['-6', '-9', '-12', '-15', '-18'];
const RAMP_OPTIONS = ['100', '300', '600'];
const MUSIC_OPTIONS = ['-3', '-6', '-9'];
const SECONDS_OPTIONS = ['0', '1', '2', '3', '5'];
const LUFS_OPTIONS = ['-14', '-16', '-23'];

/**
 * El editor de un proyecto de mezcla (spec 016, D-4): la línea de tiempo de las regiones, los controles del ducking y
 * del resultado, la vista previa con WebAudio y el render. Mientras la voz se transcribe, espera.
 */
export function MixEditor({ projectId }: { projectId: number }): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const project = useQuery({
    queryKey: ['mix', projectId],
    queryFn: () => api.get<MixProject>(`/mix/${projectId}`),
    refetchInterval: (query) => (query.state.data?.status === 'transcribing' ? 2000 : false),
  });
  const curve = useQuery({
    queryKey: ['mix', projectId, 'curve', project.data?.regions, project.data?.params],
    queryFn: () => api.get<CurveOut>(`/mix/${projectId}/curve`),
    enabled: project.data?.status === 'ready',
  });
  const save = useMutation({
    mutationFn: (body: { regions: [number, number][]; params: Partial<MixParams> }) =>
      api.put<MixProject>(`/mix/${projectId}`, body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['mix', projectId] }),
  });
  const render = useMutation({
    mutationFn: () => api.post('/jobs', { kind: 'mix.render', params: { mix_id: projectId } }),
    onSuccess: () => toast.success(t('mix.render.queued')),
    onError: (error: Error) => toast.error(error.message),
  });
  const preview = useMixPreview(curve.data?.points ?? []);

  if (!project.data) return <UIText variant="body">{t('mix.status.transcribing')}</UIText>;
  const current = project.data;
  if (current.status === 'transcribing') return <UIText variant="body">{t('mix.status.transcribing')}</UIText>;
  if (current.status === 'failed') return <UIText variant="body">{t('mix.status.failed')}</UIText>;

  const params = current.params;
  const setParam = (change: Partial<MixParams>) => save.mutate({ regions: current.regions, params: change });
  const numeric = (value: string) => Number(value);

  return (
    <UIStack gap="md">
      {/* La línea de tiempo espera a la duración: sin ella, las regiones no tienen dónde moverse. */}
      {curve.data ? (
        <MixTimeline
          regions={current.regions}
          duration={curve.data.total}
          onChange={(regions) => save.mutate({ regions, params: {} })}
        />
      ) : null}
      <UISelect
        label={t('mix.mode.label')}
        value={params.mode}
        options={[
          { value: 'transcript', label: t('mix.mode.transcript') },
          { value: 'sidechain', label: t('mix.mode.sidechain') },
        ]}
        onChange={(value) => setParam({ mode: value })}
      />
      <UISelect
        label={t('mix.duck.label')}
        value={String(params.duck_db)}
        options={DUCK_OPTIONS.map((value) => ({ value, label: value }))}
        onChange={(value) => setParam({ duck_db: numeric(value) })}
      />
      <UISelect
        label={t('mix.ramp.label')}
        value={String(params.ramp_ms)}
        options={RAMP_OPTIONS.map((value) => ({ value, label: value }))}
        onChange={(value) => setParam({ ramp_ms: numeric(value) })}
      />
      <UISelect
        label={t('mix.music.label')}
        value={String(params.music_db)}
        options={MUSIC_OPTIONS.map((value) => ({ value, label: value }))}
        onChange={(value) => setParam({ music_db: numeric(value) })}
      />
      <UISelect
        label={t('mix.intro.label')}
        value={String(params.intro)}
        options={SECONDS_OPTIONS.map((value) => ({ value, label: value }))}
        onChange={(value) => setParam({ intro: numeric(value) })}
      />
      <UISelect
        label={t('mix.outro.label')}
        value={String(params.outro)}
        options={SECONDS_OPTIONS.map((value) => ({ value, label: value }))}
        onChange={(value) => setParam({ outro: numeric(value) })}
      />
      <UISelect
        label={t('mix.lufs.label')}
        value={String(params.lufs)}
        options={LUFS_OPTIONS.map((value) => ({ value, label: value }))}
        onChange={(value) => setParam({ lufs: numeric(value) })}
      />
      <UIButton
        variant="secondary"
        onClick={() =>
          preview.active
            ? preview.stop()
            : void preview.start(api.fileUrl(current.voice), api.fileUrl(current.music), params.intro)
        }
      >
        {preview.active ? t('mix.preview.stop') : t('mix.preview.play')}
      </UIButton>
      <UIButton onClick={() => render.mutate()}>{t('mix.render')}</UIButton>
    </UIStack>
  );
}
