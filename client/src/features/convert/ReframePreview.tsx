import { useMutation, useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useRef, useState } from 'react';

import { useApi } from '@/shared/api/context';
import type { Job } from '@/shared/api/events';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { type SelectOption, UIRecommendedSelect } from '@/shared/components/molecules/UIRecommendedSelect';
import { UIRemoteImage } from '@/shared/components/molecules/UIRemoteImage';
import { type CropRect, UICropArea } from '@/shared/components/organisms/UICropArea';
import { useRecommendedValue } from '@/shared/hooks/useRecommendedValue';
import { type MessageKey, t } from '@/shared/i18n/t';

import type { Reframe } from './convertOptions';

type Props = {
  source: { path: string; width: number; height: number };
  /** El tamaño del preset de red: el rectángulo del encuadre tiene su proporción. */
  target: { width: number; height: number };
  /** Recibe el encuadre listo para el trabajo, o `null` si falta el análisis de caras. */
  onChange: (reframe: Reframe | null) => void;
};

const MODES = ['center', 'manual', 'fit-bars', 'fit-blur', 'follow-face'];

/**
 * El rectángulo de partida: el mayor de la proporción del destino que cabe en la fuente, centrado. Un 16:9 que va a 9:16
 * empieza con el alto entero y un ancho de 0,3164 del cuadro, en el centro.
 */
export function defaultRect(source: { width: number; height: number }, target: { width: number; height: number }): CropRect {
  const targetAspect = target.width / target.height;
  const sourceAspect = source.width / source.height;
  if (targetAspect <= sourceAspect) {
    const w = targetAspect / sourceAspect;
    return { x: (1 - w) / 2, y: 0, w, h: 1 };
  }
  const h = sourceAspect / targetAspect;
  return { x: 0, y: (1 - h) / 2, w: 1, h };
}

/**
 * El encuadre de Redes (D-3): el modo ★ «Centrado», el rectángulo que se arrastra en «Manual», las barras y el
 * desenfoque, y «Seguir a la persona», que necesita analizar las caras antes de poder convertir.
 *
 * @author Pablo Contreras
 * @since 2026/11/22
 */
export function ReframePreview({ source, target, onChange }: Props): React.JSX.Element {
  const api = useApi();
  const modes: SelectOption[] = MODES.map((mode) => ({
    value: mode,
    label: t(`convert.reframe.${mode}` as MessageKey),
    recommended: mode === 'center',
  }));
  const [mode] = useRecommendedValue('select.convert.reframe', modes);
  // El rectángulo que el usuario movió vale solo para este origen y este destino: si cambian, vuelve el de partida.
  // `source` y `target` llegan como objetos nuevos en cada render: el de partida se memoriza por sus números, para que
  // `reframe` no cambie de identidad en cada render (con `onChange` que actualiza el padre, eso es un ciclo infinito).
  const sizes = `${source.path}|${source.width}x${source.height}|${target.width}x${target.height}`;
  const [moved, setMoved] = useState<{ sizes: string; rect: CropRect } | null>(null);
  const { width: sourceWidth, height: sourceHeight } = source;
  const { width: targetWidth, height: targetHeight } = target;
  const start = useMemo(
    () => defaultRect({ width: sourceWidth, height: sourceHeight }, { width: targetWidth, height: targetHeight }),
    [sourceWidth, sourceHeight, targetWidth, targetHeight],
  );
  const rect = moved?.sizes === sizes ? moved.rect : start;
  const setRect = (next: CropRect) => setMoved({ sizes, rect: next });

  const [jobId, setJobId] = useState<number | null>(null);
  const analysis = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => api.get<Job>(`/jobs/${jobId}`),
    enabled: jobId !== null,
    refetchInterval: (query) => (query.state.data && ['queued', 'running'].includes(query.state.data.status) ? 1000 : false),
  });
  const track = analysis.data?.status === 'done' ? `${analysis.data.output_dir ?? ''}/track.json` : null;
  const analyze = useMutation({
    mutationFn: () => api.post<Job>('/jobs', { kind: 'media.reframe_track', params: { input: source.path } }),
    onSuccess: (job) => setJobId(job.id),
  });

  const reframe = useMemo<Reframe | null>(() => {
    if (mode === 'center') return { mode: 'center' };
    if (mode === 'manual') return { mode: 'manual', ...rect };
    if (mode === 'fit-bars') return { mode: 'fit-bars', color: 'black' };
    if (mode === 'fit-blur') return { mode: 'fit-blur', strength: 20 };
    return track ? { mode: 'follow-face', track } : null;
  }, [mode, rect, track]);
  const report = useRef(onChange);
  useEffect(() => {
    report.current = onChange;
  });
  useEffect(() => {
    report.current(reframe);
  }, [reframe]);

  const frame = api.queryUrl('/media/frame', { path: source.path, t: 0 });
  const frameText = {
    errorText: t('convert.preview.error'),
    retryLabel: t('convert.preview.retry'),
    alt: t('convert.preview.alt'),
  };
  const analyzing = analysis.data && ['queued', 'running'].includes(analysis.data.status);

  return (
    <UIStack gap="sm">
      <UIRecommendedSelect settingKey="select.convert.reframe" label={t('convert.reframe.label')} options={modes} />
      {mode === 'manual' ? (
        <>
          <UICropArea
            label={t('convert.reframe.area')}
            src={frame}
            alt={frameText.alt}
            width={source.width}
            height={source.height}
            rect={rect}
            onChange={setRect}
            errorText={frameText.errorText}
            retryLabel={frameText.retryLabel}
          />
          <UIText variant="caption">{t('convert.reframe.hint')}</UIText>
        </>
      ) : (
        <UIRemoteImage
          src={frame}
          alt={frameText.alt}
          width={source.width}
          height={source.height}
          errorText={frameText.errorText}
          retryLabel={frameText.retryLabel}
          className="block w-full"
        />
      )}
      {mode === 'follow-face' ? (
        <UIStack gap="sm">
          {analyzing ? (
            <UIText variant="caption">{t('convert.reframe.analyzing', { percent: Math.round((analysis.data?.progress ?? 0) * 100) })}</UIText>
          ) : track ? (
            <UIText variant="caption">{t('convert.reframe.ready')}</UIText>
          ) : (
            <>
              <UIText variant="caption">{t('convert.reframe.needs_analysis')}</UIText>
              <UIButton variant="secondary" className="self-start" disabled={analyze.isPending} onClick={() => analyze.mutate()}>
                {t('convert.reframe.analyze')}
              </UIButton>
            </>
          )}
        </UIStack>
      ) : null}
    </UIStack>
  );
}
