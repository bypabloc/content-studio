import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { t } from '@/shared/i18n/t';
import { Player } from '@/shared/media/Player';
import { useMediaInfo, useMediaPeaks } from '@/shared/media/useMediaInfo';

type Job = components['schemas']['Job'];

/** `script.json` de la carpeta de un trabajo: el nombre de su .wav y los párrafos tal como se pidieron. */
interface Script {
  wav: string;
  segments: { text: string }[];
}

/** El `.json` de la toma: la evaluación de whisper por párrafo, o null si no se evaluó (`save_metadata`). */
interface Take {
  evaluation: { observations: string[] } | null;
}

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
 * párrafo encola `narration.regenerate` sobre este trabajo (AC-8, D-4).
 */
export function NarrationResult({ job }: { job: Job }) {
  const api = useApi();
  const queryClient = useQueryClient();
  const folder = job.output_dir ?? '';
  const inFolder = (name: string) => `${folder}/${name}`;
  const script = useQuery({
    queryKey: ['takes', folder, 'script'],
    queryFn: () => api.get<Script>(`/files?path=${encodeURIComponent(inFolder('script.json'))}`),
    enabled: folder !== '',
  });
  const wav = script.data ? inFolder(script.data.wav) : '';
  const take = useQuery({
    queryKey: ['takes', wav, 'json'],
    queryFn: () => api.get<Take>(`/files?path=${encodeURIComponent(wav.replace(/\.wav$/, '.json'))}`),
    enabled: wav !== '',
  });
  const info = useMediaInfo(wav);
  const peaks = useMediaPeaks(wav);
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
      <h2 className="text-sm font-medium">{t('narration.result.title')}</h2>
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
    </section>
  );
}
