import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useApi } from '@/shared/api/context';
import { useShortcut } from '@/shared/hooks/useShortcut';
import { t } from '@/shared/i18n/t';
import { NarrationOptions } from './NarrationOptions';
import { ScriptEditor } from './ScriptEditor';
import { narrationParams, useNarrationChoice } from './useNarrationChoice';
import { useScriptLint } from './useScriptLint';

/**
 * La sección Narración: el guion a la izquierda y las opciones a la derecha. Generar (botón o Ctrl+Enter) encola un
 * trabajo; los avisos del linter no lo bloquean (AC-8). Lo que se importa encola un trabajo por archivo (AC-9).
 */
export function NarrationPage() {
  const api = useApi();
  const queryClient = useQueryClient();
  const choice = useNarrationChoice();
  const [text, setText] = useState('');
  const issues = useScriptLint(text, choice.style).data?.issues.length ?? 0;
  const enqueue = useMutation({
    mutationFn: (params: Record<string, unknown>) => api.post('/jobs', { kind: 'narration', params }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });

  const generate = () => {
    if (text.trim()) enqueue.mutate(narrationParams(choice, { text }));
  };
  useShortcut('mod+enter', (event) => {
    event.preventDefault();
    generate();
  });

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
      <ScriptEditor
        value={text}
        narrationStyle={choice.style}
        onChange={setText}
        onImport={(paths) => paths.forEach((file) => enqueue.mutate(narrationParams(choice, { file: [file] })))}
      />
      <aside className="flex flex-col gap-6">
        <NarrationOptions />
        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={generate}
            disabled={!text.trim()}
            title={t('narration.generate.shortcut')}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {t('narration.generate')}
          </button>
          {issues > 0 && <p className="text-sm text-muted-foreground">{t('narration.generate.warnings', { count: issues })}</p>}
        </div>
      </aside>
    </div>
  );
}
