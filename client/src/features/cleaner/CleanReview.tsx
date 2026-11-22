import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';

import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIMedia } from '@/shared/components/atoms/UIMedia';
import { UISkeleton } from '@/shared/components/atoms/UISkeleton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { UIField } from '@/shared/components/molecules/UIField';
import { UISwitch } from '@/shared/components/atoms/UISwitch';
import { t } from '@/shared/i18n/t';
import { useMediaPeaks } from '@/shared/media/useMediaInfo';
import { useSyncedMedia } from '@/shared/media/useSyncedMedia';

import { ReviewWave } from './ReviewWave';
import { type Cut, clock, keepDuration, moveSelection, skipTarget, toggleCut } from './cuts';

/** Lo que guarda `cuts.json` en la carpeta del análisis (spec 013, D-3 a D-5). */
interface CleanDocument {
  params: { input?: string; min_gap?: number; padding?: number; edges?: boolean };
  duration: number;
  transcript: string;
  cuts: Cut[];
}
interface Word {
  start: number;
  end: number;
  word: string;
}
interface Transcript {
  segments: Array<{ words: Word[] }>;
}
interface PlanValues {
  min_gap: number;
  padding: number;
  edges: boolean;
}
/** Un trabajo del limpiador: su id, su carpeta de salida y sus parámetros (spec 014, AC-11). */
interface CleanJob {
  id: number;
  status: string;
  output_dir: string;
  params: Record<string, unknown>;
}

const VIDEO_EXTENSIONS = ['.mp4', '.mov', '.mkv', '.webm', '.avi', '.m4v'];

function isVideo(path: string): boolean {
  const lower = path.toLowerCase();
  return VIDEO_EXTENSIONS.some((extension) => lower.endsWith(extension));
}

// En un campo de texto las teclas son letras: ahí no mueven la revisión.
function isTyping(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName));
}

// Un número escrito a medias ('' o '-') cuenta como 0, no como NaN.
function number(raw: string): number {
  const value = Number(raw);
  return raw !== '' && Number.isFinite(value) ? value : 0;
}

/**
 * La revisión de un análisis (spec 013, D-6, AC-7): el video o el audio con su onda, los cortes como regiones, la
 * transcripción, los márgenes que replanifican sin GPU, «Escuchar sin cortes» y los atajos. «Renderizar» guarda los cortes
 * y encola `clean.render`.
 */
export function CleanReview({ jobId, onBack }: { jobId: number; onBack?: () => void }): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const analysis = useQuery({
    queryKey: ['clean', jobId],
    queryFn: () => api.get<CleanDocument>(`/clean/${jobId}`),
    staleTime: Infinity,
  });
  const transcript = useQuery({
    queryKey: ['clean', jobId, 'transcript'],
    queryFn: () => api.get<Transcript>(`/files?path=${encodeURIComponent(analysis.data?.transcript ?? '')}`),
    enabled: analysis.data !== undefined,
    staleTime: Infinity,
  });
  const input = analysis.data?.params.input ?? '';
  const peaks = useMediaPeaks(input);

  const [cuts, setCuts] = useState<Cut[]>([]);
  const [selected, setSelected] = useState(0);
  const [preview, setPreview] = useState(false);
  const [minGap, setMinGap] = useState(500);
  const [padding, setPadding] = useState(150);
  const [edges, setEdges] = useState(true);
  const [media, setMedia] = useState<HTMLMediaElement | null>(null);
  const [seeded, setSeeded] = useState<CleanDocument | null>(null);
  const skip = preview ? (seconds: number) => skipTarget(seconds, cuts) : undefined;
  const { time, playing, seek, toggle } = useSyncedMedia(media, skip);

  // Al llegar el documento, sus cortes y márgenes pasan al estado. Se ajusta durante el render, sin efecto.
  if (analysis.data && analysis.data !== seeded) {
    setSeeded(analysis.data);
    setCuts(analysis.data.cuts);
    setMinGap(Math.round((analysis.data.params.min_gap ?? 0.5) * 1000));
    setPadding(Math.round((analysis.data.params.padding ?? 0.15) * 1000));
    setEdges(analysis.data.params.edges ?? true);
  }

  // Solo cuenta la respuesta del último cambio: una respuesta vieja no pisa los cortes de un valor más nuevo.
  const planned = useRef<PlanValues | null>(null);
  const replan = useMutation({
    mutationFn: (values: PlanValues) => api.post<CleanDocument>(`/clean/${jobId}/plan`, values),
    onSuccess: (next, values) => {
      if (values === planned.current) setCuts(next.cuts);
    },
  });
  function replanWith(values: PlanValues) {
    planned.current = values;
    replan.mutate(values);
  }

  const render = useMutation({
    mutationFn: async () => {
      await api.put(`/clean/${jobId}/cuts`, { cuts });
      return api.post(`/clean/${jobId}/render`);
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });

  // «Subtitular» (AC-11): el video limpio de la última render de este análisis. Sin render, el botón espera.
  const renders = useQuery({
    queryKey: ['jobs', 'clean.render'],
    queryFn: () => api.get<CleanJob[]>('/jobs?kind=clean.render'),
  });
  // La render guarda la carpeta de salida de su análisis. El transcript no sirve para ligarlas: vive en la caché de transcripción.
  const analyses = useQuery({
    queryKey: ['jobs', 'clean.analyze'],
    queryFn: () => api.get<CleanJob[]>('/jobs?kind=clean.analyze'),
  });
  const folderOf = (path: unknown) => String(path ?? '').replace(/\\/g, '/');
  const analysisDir = (analyses.data ?? []).find((job) => job.id === jobId)?.output_dir ?? '';
  const analysisFolder = folderOf(analysisDir);
  const cleanRender = (renders.data ?? []).find(
    (job) => job.status === 'done' && analysisFolder !== '' && folderOf(job.params.analysis) === analysisFolder,
  );
  const cleanSource = cleanRender ? `${cleanRender.output_dir}/clean.${/\.(mp4|mov|mkv|webm|avi|m4v)$/i.test(input) ? 'mp4' : 'wav'}` : null;
  const subtitle = useMutation({
    mutationFn: () =>
      api.post('/jobs', {
        kind: 'subtitles.create',
        params: { origin: 'cleaner', input: analysis.data?.transcript, analysis: analysisDir, source: cleanSource },
      }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (isTyping(event.target)) return;
      if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
        event.preventDefault();
        const next = moveSelection(selected, cuts.length, event.key === 'ArrowRight' ? 1 : -1);
        setSelected(next);
        if (cuts[next]) seek(cuts[next].start);
      } else if (event.key === 'd' || event.key === 'D') {
        setCuts((current) => toggleCut(current, selected));
      } else if (event.key === ' ' && !(event.target instanceof HTMLButtonElement)) {
        event.preventDefault();
        toggle();
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [cuts, selected, seek, toggle]);

  if (!analysis.data) return <UISkeleton className="h-64 w-full rounded-xl" />;

  const data = analysis.data;
  const keep = keepDuration(data.duration, cuts);
  const words = (transcript.data?.segments ?? []).flatMap((segment) => segment.words);
  const currentWord = words.findIndex((word) => time >= word.start && time < word.end);

  return (
    <UIStack gap="md">
      {onBack ? (
        <UIButton variant="secondary" className="self-start" onClick={onBack}>
          {t('cleaner.review.back')}
        </UIButton>
      ) : null}
      <UIMedia
        kind={isVideo(input) ? 'video' : 'audio'}
        src={api.fileUrl(input)}
        className="w-full rounded-xl bg-black"
        mediaRef={setMedia}
      />
      {media && peaks.data ? (
        <ReviewWave
          media={media}
          peaks={peaks.data.peaks}
          duration={data.duration}
          cuts={cuts}
          selected={selected}
          onCutsChange={setCuts}
          onSelect={setSelected}
        />
      ) : null}
      <UIStack direction="row" align="center" gap="sm">
        <UIIconButton
          variant="primary"
          icon={playing ? 'pause' : 'play'}
          label={playing ? t('action.pause') : t('action.play')}
          onClick={toggle}
          className="size-11 shrink-0 rounded-full px-0"
        />
        <UIText variant="caption">{t('cleaner.review.duration', { duration: clock(keep) })}</UIText>
        <UIButton variant={preview ? 'primary' : 'secondary'} aria-pressed={preview} onClick={() => setPreview(!preview)}>
          {t('cleaner.review.preview')}
        </UIButton>
        <UIButton disabled={render.isPending} onClick={() => render.mutate()}>
          {t('cleaner.review.render')}
        </UIButton>
        <UIButton variant="secondary" disabled={!cleanSource || subtitle.isPending} onClick={() => subtitle.mutate()}>
          {t('cleaner.review.subtitle')}
        </UIButton>
      </UIStack>
      <UIStack direction="row" align="end" gap="sm">
        <UIField
          type="number"
          min={0}
          label={t('cleaner.options.min_gap')}
          value={minGap}
          onChange={(event) => {
            setMinGap(number(event.target.value));
            replanWith({ min_gap: number(event.target.value) / 1000, padding: padding / 1000, edges });
          }}
        />
        <UIField
          type="number"
          min={0}
          label={t('cleaner.options.padding')}
          value={padding}
          onChange={(event) => {
            setPadding(number(event.target.value));
            replanWith({ min_gap: minGap / 1000, padding: number(event.target.value) / 1000, edges });
          }}
        />
        <UISwitch
          label={t('cleaner.options.edges')}
          checked={edges}
          onChange={(value) => {
            setEdges(value);
            replanWith({ min_gap: minGap / 1000, padding: padding / 1000, edges: value });
          }}
        />
      </UIStack>
      <UIText variant="caption">{t('cleaner.review.shortcuts')}</UIText>
      <UIStack gap="xs">
        {cuts.map((cut, index) => (
          <UIButton
            key={index}
            variant={index === selected ? 'primary' : 'ghost'}
            aria-pressed={index === selected}
            onClick={() => {
              setSelected(index);
              seek(cut.start);
            }}
          >
            {t('cleaner.review.cut', {
              number: index + 1,
              start: clock(cut.start),
              end: clock(cut.end),
              state: cut.enabled ? t('cleaner.review.cut.on') : t('cleaner.review.cut.off'),
            })}
          </UIButton>
        ))}
      </UIStack>
      <UIText variant="subtitle">{t('cleaner.review.transcript')}</UIText>
      <UIStack direction="row" gap="xs" className="flex-wrap">
        {words.map((word, index) => (
          <UIButton key={index} variant={index === currentWord ? 'primary' : 'ghost'} onClick={() => seek(word.start)}>
            {word.word}
          </UIButton>
        ))}
      </UIStack>
    </UIStack>
  );
}
