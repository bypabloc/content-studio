import { useId } from 'react';
import { t } from '@/shared/i18n/t';
import { EDITOR_TEXT, ScriptHighlight } from './ScriptHighlight';
import { useScriptImport } from './useScriptImport';
import { useScriptLint } from './useScriptLint';

/**
 * El guion: un campo con los avisos del linter subrayados (AC-6), las palabras y la duración que estima el server, y
 * «Importar». Los avisos no bloquean nada: la pantalla decide qué hacer con ellos.
 */
export function ScriptEditor({
  value,
  narrationStyle,
  onChange,
  onImport,
}: {
  value: string;
  narrationStyle: string;
  onChange: (text: string) => void;
  onImport: (paths: string[]) => void;
}) {
  const id = useId();
  const lint = useScriptLint(value, narrationStyle);
  const { pick } = useScriptImport(onImport);
  const issues = lint.data?.issues ?? [];

  return (
    <section className="flex flex-col gap-2">
      <label htmlFor={id} className="text-sm font-medium">
        {t('narration.editor.label')}
      </label>
      <div className="relative min-h-64 rounded-md border border-input bg-background focus-within:ring-2 focus-within:ring-ring">
        <ScriptHighlight text={value} issues={issues} />
        <textarea
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={t('narration.editor.placeholder')}
          spellCheck={false}
          className={`${EDITOR_TEXT} relative min-h-64 w-full resize-y bg-transparent outline-none`}
        />
      </div>
      <footer className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
        {lint.data && (
          <span>{t('narration.editor.stats', { words: lint.data.words, seconds: Math.round(lint.data.seconds) })}</span>
        )}
        <span>
          {issues.length === 1
            ? t('narration.editor.issues_one')
            : t('narration.editor.issues_other', { count: issues.length })}
        </span>
        <button
          type="button"
          onClick={() => void pick()}
          className="ml-auto rounded-md border border-border px-3 py-1.5 text-foreground hover:bg-accent"
        >
          {t('narration.import.button')}
        </button>
      </footer>
    </section>
  );
}
