import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { useShortcut } from '@/shared/hooks/useShortcut';
import { t } from '@/shared/i18n/t';
import { NarrationOptions } from './NarrationOptions';
import { NarrationResult } from './NarrationResult';
import { ScriptEditor } from './ScriptEditor';
import { narrationParams, useNarrationChoice } from './useNarrationChoice';
import { useScriptLint } from './useScriptLint';

type Job = components['schemas']['Job'];

// Los trabajos que dejan una toma: la narración y la regeneración de un párrafo.
const TAKE_KINDS = ['narration', 'narration.regenerate'];

/** La toma más reciente que ya terminó; los trabajos en cola o de música no cuentan. */
function latestTake(jobs: Job[]): Job | undefined {
  return jobs.filter((job) => job.status === 'done' && TAKE_KINDS.includes(job.kind)).sort((a, b) => b.id - a.id)[0];
}

/**
 * La sección Narración: el guion a la izquierda y las opciones a la derecha. Generar (botón o Ctrl+Enter) encola un
 * trabajo; los avisos del linter no lo bloquean (AC-8). Lo que se importa encola un trabajo por archivo (AC-9). Debajo
 * del guion sale la última toma terminada.
 */
export function NarrationPage() {
  const api = useApi();
  const queryClient = useQueryClient();
  const choice = useNarrationChoice();
  const [text, setText] = useState('');
  const issues = useScriptLint(text, choice.style).data?.issues.length ?? 0;
  const jobs = useQuery({ queryKey: ['jobs'], queryFn: () => api.get<Job[]>('/jobs') });
  const take = latestTake(jobs.data ?? []);
  const enqueue = useMutation({
    mutationFn: (params: Record<string, unknown>) => api.post('/jobs', { kind: 'narration', params }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });

  // Sin catálogo no hay motor ni estilo que mandar: Generar e importar esperan a que llegue (no encolan un trabajo vacío).
  const ready = choice.model !== '' && choice.style !== '';
  const generate = () => {
    if (ready && text.trim()) enqueue.mutate(narrationParams(choice, { text }));
  };
  const importFiles = (paths: string[]) => {
    if (ready) paths.forEach((file) => enqueue.mutate(narrationParams(choice, { file: [file] })));
  };
  useShortcut('mod+enter', (event) => {
    event.preventDefault();
    generate();
  });

  // En escritorio, el guion y las opciones van en dos columnas (1fr y 20 rem); en pantallas chicas, una debajo de otra.
  return (
    <UIStack gap="lg" className="lg:flex-row lg:items-start">
      <UIStack gap="lg" className="min-w-0 lg:flex-1">
        <ScriptEditor value={text} narrationStyle={choice.style} onChange={setText} onImport={importFiles} />
        {take && <NarrationResult job={take} />}
      </UIStack>
      <UIStack role="complementary" gap="lg" className="lg:w-80 lg:shrink-0">
        <NarrationOptions />
        <UIStack gap="sm">
          <UIButton variant="primary" onClick={generate} disabled={!text.trim() || !ready} title={t('narration.generate.shortcut')}>
            {t('narration.generate')}
          </UIButton>
          {issues > 0 && (
            <UIText variant="caption">
              {issues === 1
                ? t('narration.generate.warnings_one')
                : t('narration.generate.warnings_other', { count: issues })}
            </UIText>
          )}
        </UIStack>
      </UIStack>
    </UIStack>
  );
}
