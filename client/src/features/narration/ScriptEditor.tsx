import { useId } from 'react';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UITextarea } from '@/shared/components/molecules/UITextarea';
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
    <UIStack gap="sm">
      {/* La etiqueta visible va como texto; el campo la lleva oculta, para que sus avisos queden alineados detrás. */}
      <UIText variant="body" className="text-sm font-medium text-foreground">
        {t('narration.editor.label')}
      </UIText>
      <UIStack className="relative min-h-64">
        <ScriptHighlight text={value} issues={issues} />
        <UITextarea
          id={id}
          label={t('narration.editor.label')}
          hideLabel
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={t('narration.editor.placeholder')}
          spellCheck={false}
          className={`${EDITOR_TEXT} relative min-h-64 w-full resize-y bg-transparent outline-none`}
        />
      </UIStack>
      <UIStack direction="row" align="center" gap="sm" className="flex-wrap">
        {lint.data && (
          <UIText variant="caption">
            {t('narration.editor.stats', { words: lint.data.words, seconds: Math.round(lint.data.seconds) })}
          </UIText>
        )}
        <UIText variant="caption">
          {issues.length === 1
            ? t('narration.editor.issues_one')
            : t('narration.editor.issues_other', { count: issues.length })}
        </UIText>
        <UIIconButton variant="secondary" icon="import-file" label={t('action.import')} className="ml-auto size-11 px-0" onClick={() => void pick()} />
      </UIStack>
    </UIStack>
  );
}
