import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { useEffect, useState } from 'react';

import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIRecommendedSelect } from '@/shared/components/molecules/UIRecommendedSelect';
import { useSetting } from '@/shared/hooks/useSetting';
import { label, t } from '@/shared/i18n/t';
import { Player } from '@/shared/media/Player';
import { useMediaPeaks } from '@/shared/media/useMediaInfo';

import { DurationField } from './DurationField';
import { FreeTextStyle, type FreeText, freeTextComplete } from './FreeTextStyle';
import { MusicCompare } from './MusicCompare';
import { MusicOptions } from './MusicOptions';
import { StyleBrowser } from './StyleBrowser';
import { useMatchDuration } from './useMatchDuration';
import { useMatchSources } from './useMatchSources';

type StylesOut = components['schemas']['StylesOut'];
type EngineInfo = components['schemas']['EngineInfo'];

/** Motores de música (spec 011, D-6): ACE-Step es el recomendado. Sus máximos son los del server (`MusicSpec`). */
type Job = components['schemas']['Job'];
const ENGINES = [
  { id: 'acestep', max: 600, recommended: true },
  { id: 'heartmula', max: 240, recommended: false },
];
const MEDIA_EXTENSIONS = ['wav', 'mp3', 'flac', 'ogg', 'm4a', 'mp4', 'mov', 'mkv', 'webm'];

/** La muestra de 10 s de un preset, con su onda (solo si ya existe). */
function SamplePlayer({ path }: { path: string }): React.JSX.Element | null {
  const api = useApi();
  const peaks = useMediaPeaks(path);
  return peaks.data ? <Player src={api.fileUrl(path)} peaks={peaks.data.peaks} /> : null;
}

/**
 * Sección Música (spec 011, D-6): motor, duración, estilos y «Avanzado» en una pantalla. Generar encola un solo
 * trabajo `music` con todos los estilos elegidos; sus pistas comparten `group_key`.
 */
export function MusicPage(): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const catalog = useQuery({ queryKey: ['music', 'styles'], queryFn: () => api.get<StylesOut>('/music/styles') });
  const engines = useQuery({ queryKey: ['engines'], queryFn: () => api.get<EngineInfo[]>('/engines') });
  const sources = useMatchSources();
  const matched = useMatchDuration();
  const [model] = useSetting<string>('select.music.model', 'acestep');
  const [favorites, setFavorites] = useSetting<string[]>('music.favorites', []);
  const [tail, setTail] = useSetting<number>('music.match_tail', 2);
  const [selected, setSelected] = useState<string[]>([]);
  const [duration, setDuration] = useState(60);
  const [variants, setVariants] = useState(1);
  const [noLm, setNoLm] = useState(false);
  const [evaluate, setEvaluate] = useState(true);
  const [retries, setRetries] = useState(1);
  const [sampleKey, setSampleKey] = useState<string | null>(null);
  const [mode, setMode] = useState<'presets' | 'free'>('presets');
  const [free, setFree] = useState<FreeText>({ caption: '', key: null, bpm: null, timeSignature: '4' });
  const [group, setGroup] = useState<string | null>(null);

  const max = ENGINES.find((engine) => engine.id === model)?.max ?? 600;
  const selectedEngine = engines.data?.find((engine) => engine.engine === model);
  const engineMissing = selectedEngine && !['installed', 'external'].includes(selectedEngine.status);
  const freeReady = freeTextComplete(free);
  const ready = mode === 'presets' ? selected.length > 0 : freeReady;
  const generate = useMutation({
    mutationFn: () =>
      api.post<Job>('/jobs', {
        kind: 'music',
        params: {
          model,
          // Un estilo de preset va por su clave; el texto libre, como texto con su tonalidad, BPM y compás (D-5).
          ...(mode === 'presets'
            ? { style: selected }
            : { style: [free.caption.trim()], key: free.key, bpm: free.bpm, time_signature: free.timeSignature }),
          duration,
          variants,
          no_lm: noLm,
          evaluate,
          retries,
        },
      }),
    onSuccess: (job) => {
      setGroup(job.group_key ?? null);
      void queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
  const { mutate } = generate;

  // Con `?match=` (Mezcla), la duración es la de la voz más la cola: se fija una vez al llegar.
  const [appliedMatch, setAppliedMatch] = useState<number | null>(null);
  if (matched !== null && matched !== appliedMatch) {
    setAppliedMatch(matched);
    setDuration(matched);
  }

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.ctrlKey && event.key === 'Enter' && ready) mutate();
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [mutate, ready]);

  async function pickMediaDuration(): Promise<number | null> {
    const chosen = await open({
      multiple: false,
      filters: [{ name: t('music.media.filter'), extensions: MEDIA_EXTENSIONS }],
    });
    if (typeof chosen !== 'string') return null;
    const info = await api.get<{ duration: number }>(`/media/info?path=${encodeURIComponent(chosen)}`);
    return info.duration;
  }

  const styles = catalog.data?.styles ?? [];
  const sample = styles.find((style) => style.key === sampleKey)?.sample ?? null;
  const toggle = (list: string[], key: string) => (list.includes(key) ? list.filter((item) => item !== key) : [...list, key]);
  const stableKeys = [...new Set(styles.map((style) => style.musical_key))].sort();

  return (
    <UIStack gap="lg">
      <UIRecommendedSelect
        settingKey="select.music.model"
        label={t('music.options.engine')}
        options={ENGINES.map((engine) => ({
          value: engine.id,
          label: engine.id,
          recommended: engine.recommended,
          hint: label('music.model', engine.id),
        }))}
      />
      {engineMissing ? (
        <UIButton variant="secondary" className="self-start" onClick={() => { window.location.hash = `#/engines?engine=${encodeURIComponent(model)}`; }}>
          {t('engines.install_from_options')}
        </UIButton>
      ) : null}
      <DurationField
        value={duration}
        max={max}
        tail={tail}
        matchSources={sources}
        onChange={setDuration}
        onTailChange={setTail}
        pickMediaDuration={pickMediaDuration}
      />
      <UIStack direction="row" gap="sm">
        <UIButton variant={mode === 'presets' ? 'primary' : 'secondary'} aria-pressed={mode === 'presets'} onClick={() => setMode('presets')}>
          {t('music.mode.presets')}
        </UIButton>
        <UIButton variant={mode === 'free' ? 'primary' : 'secondary'} aria-pressed={mode === 'free'} onClick={() => setMode('free')}>
          {t('music.mode.free')}
        </UIButton>
      </UIStack>
      {mode === 'presets' ? (
        <StyleBrowser
          styles={styles}
          favorites={favorites}
          selected={selected}
          onToggleFavorite={(key) => setFavorites(toggle(favorites, key))}
          onToggleSelect={(key) => setSelected(toggle(selected, key))}
          onPlay={setSampleKey}
        />
      ) : (
        <FreeTextStyle value={free} keys={stableKeys} onChange={setFree} />
      )}
      {sample ? <SamplePlayer path={sample} /> : null}
      <MusicOptions
        variants={variants}
        onVariants={setVariants}
        noLm={noLm}
        onNoLm={setNoLm}
        evaluate={evaluate}
        onEvaluate={setEvaluate}
        retries={retries}
        onRetries={setRetries}
      />
      <UIButton disabled={!ready || generate.isPending} onClick={() => mutate()}>
        {t('music.generate')}
      </UIButton>
      {group ? <MusicCompare groupKey={group} /> : null}
    </UIStack>
  );
}
