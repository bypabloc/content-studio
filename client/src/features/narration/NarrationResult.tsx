import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useApi } from '@/shared/api/context';
import { t } from '@/shared/i18n/t';
import { Player } from '@/shared/media/Player';
import { CompareTakes } from './CompareTakes';
import { type Job, useTake } from './useTake';

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

  if (!script.data) return null;
  const evaluated = take.data?.evaluation ?? null;
  const notes = (evaluated?.observations ?? []).map(parseNote);
  const others = notes.filter((note) => note.paragraph === undefined);

  return (
    <section aria-label={t('narration.result.title')} className="flex flex-col gap-4 rounded-md border border-border p-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-medium">{t('narration.result.title')}</h2>
        {job.group_key && (
          <button
            type="button"
            aria-expanded={comparing}
            onClick={() => setComparing((open) => !open)}
            className="rounded-md border border-border px-2 py-1 text-xs hover:bg-accent"
          >
            {t('narration.compare.open')}
          </button>
        )}
      </div>
      {peaks.data && <Player src={api.fileUrl(wav)} peaks={peaks.data.peaks} />}
      {info.data && (
        <p className="text-sm text-muted-foreground">
          {t('narration.result.loudness', {
            lufs: info.data.lufs.toFixed(1),
            peak: info.data.true_peak.toFixed(1),
          })}
        </p>
      )}
      {take.isSuccess && !evaluated && <p className="text-sm">{t('narration.result.unevaluated')}</p>}
      <ol className="flex flex-col gap-3">
        {script.data.segments.map((segment, index) => (
          <li key={index} className="flex flex-col gap-1">
            <div className="flex items-start gap-3">
              <span className="w-6 shrink-0 text-right text-sm text-muted-foreground">{`${index + 1}.`}</span>
              <p className="flex-1 text-sm">{segment.text}</p>
              <button
                type="button"
                onClick={() => regenerate.mutate(index)}
                className="shrink-0 rounded-md border border-border px-2 py-1 text-xs hover:bg-accent"
              >
                {t('narration.result.regenerate')}
              </button>
            </div>
            {notes
              .filter((note) => note.paragraph === index + 1)
              .map((note, k) => (
                <p key={k} className="pl-9 text-sm">
                  {note.diff ? (
                    <>
                      {note.diff.label} <del>{note.diff.expected}</del> <ins>{note.diff.said}</ins>
                    </>
                  ) : (
                    note.text
                  )}
                </p>
              ))}
          </li>
        ))}
      </ol>
      {others.length > 0 && (
        <div className="flex flex-col gap-1">
          <h3 className="text-xs font-medium text-muted-foreground">{t('narration.result.other')}</h3>
          {others.map((note, k) => (
            <p key={k} className="text-sm text-muted-foreground">
              {note.text}
            </p>
          ))}
        </div>
      )}
      {comparing && job.group_key && <CompareTakes groupKey={job.group_key} />}
    </section>
  );
}
