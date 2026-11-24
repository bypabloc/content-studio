import { useMutation, useQueryClient } from '@tanstack/react-query';
import { lazy, Suspense, useState } from 'react';
import { useApi } from '@/shared/api/context';
import { UIDiffText } from '@/shared/components/atoms/UIDiffText';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { Player } from '@/shared/media/Player';
import { sendTo } from '@/shared/navigation/sendTo';
import { CompareTakes } from './CompareTakes';
import { type Job, useTake } from './useTake';

const OpenInEditorButton = lazy(() =>
  import('@/shared/navigation/OpenInEditorButton').then((module) => ({ default: module.OpenInEditorButton })),
);

type DiffKind = 'change' | 'missing' | 'extra';

/** Una observación del motor: un cambio de palabras (`diff`), o un aviso de silencio o de ritmo (`text`). */
interface Note {
  paragraph?: number;
  text?: string;
  diff?: { label: string; expected: string; said: string };
}

/** El texto de cada tipo de diferencia de `narration/evaluation/compare.py`. */
function diffLabel(kind: DiffKind): string {
  if (kind === 'change') return t('narration.result.diff.change');
  if (kind === 'missing') return t('narration.result.diff.missing');
  return t('narration.result.diff.extra');
}

/** Lee una observación de `narration/evaluation/review.py` (en inglés) y la deja lista para mostrarla en español. */
function parseNote(line: string): Note {
  const diff = /^paragraph (\d+): (change|missing|extra) "(.*)" -> "(.*)"$/.exec(line);
  if (diff) {
    return { paragraph: Number(diff[1]), diff: { label: diffLabel(diff[2] as DiffKind), expected: diff[3], said: diff[4] } };
  }
  const silence = /^paragraph (\d+): ([\d.]+) s of silence inside the paragraph$/.exec(line);
  if (silence) return { paragraph: Number(silence[1]), text: t('narration.result.silence', { seconds: silence[2] }) };
  const rhythm = /^notice, paragraph (\d+): rhythm ([\d.]+) words\/s \(median ([\d.]+)\)$/.exec(line);
  if (rhythm) {
    return { paragraph: Number(rhythm[1]), text: t('narration.result.rhythm', { speed: rhythm[2], median: rhythm[3] }) };
  }
  return { text: line };
}

/**
 * El resultado de una toma: su onda, su LUFS y su pico, y cada párrafo con lo que whisper oyó distinto. Regenerar un
 * párrafo encola `narration.regenerate` sobre este trabajo (AC-8, D-4). «Comparar» abre las tomas del mismo texto.
 */
export function NarrationResult({ job }: { job: Job }) {
  const api = useApi();
  const queryClient = useQueryClient();
  const [comparing, setComparing] = useState(false);
  const { wav, script, take, info, peaks } = useTake(job);
  const regenerate = useMutation({
    mutationFn: (index: number) =>
      api.post('/jobs', { kind: 'narration.regenerate', params: { source_job: job.id, index } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });
  // «Subtitular» (spec 014, D-4): el texto de los cues es el del guion; los tiempos salen de alinear la toma.
  const subtitle = useMutation({
    mutationFn: () =>
      api.post('/jobs', {
        kind: 'subtitles.create',
        params: {
          origin: 'narration',
          input: wav,
          source: wav,
          script: (script.data?.segments ?? []).map((segment) => segment.text).join(' '),
          language: 'es',
        },
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });

  if (!script.data) return null;
  const evaluated = take.data?.evaluation ?? null;
  const notes = (evaluated?.observations ?? []).map(parseNote);
  const others = notes.filter((note) => note.paragraph === undefined);

  return (
    <UIStack role="region" aria-label={t('narration.result.title')} gap="md" className="rounded-md border border-border p-4">
      <UIStack direction="row" justify="between" align="center" gap="sm">
        <UIText variant="subtitle" className="text-sm">
          {t('narration.result.title')}
        </UIText>
        {job.group_key && (
          <UIIconButton
            variant="secondary"
            icon="compare"
            label={t('action.compare')}
            aria-expanded={comparing}
            onClick={() => setComparing((open) => !open)}
          />
        )}
      </UIStack>
      {peaks.data && <Player src={api.fileUrl(wav)} peaks={peaks.data.peaks} />}
      <UIStack direction="row" gap="sm">
        <Suspense fallback={null}>
          <OpenInEditorButton paths={wav ? [wav] : []} />
        </Suspense>
        <UIButton variant="secondary" disabled={subtitle.isPending} onClick={() => subtitle.mutate()}>
          {t('narration.result.subtitle')}
        </UIButton>
        <UIButton variant="secondary" disabled={!wav} onClick={() => sendTo('mix', wav)}>
          {t('mix.send')}
        </UIButton>
      </UIStack>
      {info.data && (
        <UIText variant="caption">
          {t('narration.result.loudness', {
            lufs: info.data.lufs.toFixed(1),
            peak: info.data.true_peak.toFixed(1),
          })}
        </UIText>
      )}
      {take.isSuccess && !evaluated && (
        <UIText variant="body" className="text-sm">
          {t('narration.result.unevaluated')}
        </UIText>
      )}
      <UIStack role="list" gap="md">
        {script.data.segments.map((segment, index) => (
          <UIStack key={index} role="listitem" gap="sm">
            <UIStack direction="row" align="start" gap="md">
              <UIText variant="caption" className="w-6 shrink-0 text-right text-sm">
                {`${index + 1}.`}
              </UIText>
              <UIText variant="body" className="flex-1 text-sm">
                {segment.text}
              </UIText>
              <UIIconButton
                variant="secondary"
                icon="regenerate"
                label={t('action.regenerate')}
                className="shrink-0 size-11 px-0"
                onClick={() => regenerate.mutate(index)}
              />
            </UIStack>
            {notes
              .filter((note) => note.paragraph === index + 1)
              .map((note, k) => (
                <UIText key={k} variant="body" className="pl-9 text-sm">
                  {note.diff ? (
                    <UIDiffText label={note.diff.label} expected={note.diff.expected} said={note.diff.said} />
                  ) : (
                    note.text
                  )}
                </UIText>
              ))}
          </UIStack>
        ))}
      </UIStack>
      {others.length > 0 && (
        <UIStack gap="sm">
          <UIText variant="heading" className="text-xs text-muted-foreground">
            {t('narration.result.other')}
          </UIText>
          {others.map((note, k) => (
            <UIText key={k} variant="caption">
              {note.text}
            </UIText>
          ))}
        </UIStack>
      )}
      {comparing && job.group_key && <CompareTakes groupKey={job.group_key} />}
    </UIStack>
  );
}
