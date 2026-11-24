import { AssistantButton } from '@/features/assistant/AssistantButton';
import { useAssistantTask } from '@/features/assistant/useAssistant';
import { t } from '@/shared/i18n/t';

import { type ReviewedParagraph, ScriptReviewDiff } from './ScriptReviewDiff';

interface Review {
  paragraphs: ReviewedParagraph[];
  discarded: { index: number }[];
}

const PARAGRAPH = /\n[ \t]*\n/;

/** El guion con un párrafo reemplazado; si el texto cambió mientras tanto, busca el párrafo original por su contenido. */
export function replaceParagraph(text: string, paragraph: ReviewedParagraph): string {
  const paragraphs = text.trim().split(PARAGRAPH);
  const index = paragraphs[paragraph.index] === paragraph.original ? paragraph.index : paragraphs.indexOf(paragraph.original);
  if (index < 0) return text;
  paragraphs[index] = paragraph.revised;
  return paragraphs.join('\n\n');
}

/** «Revisar con IA» (spec 021, D-5): encola `llm.script_review` y muestra el diff; aceptar cambia el texto del editor. */
export function ScriptReview({
  text,
  onChange,
}: {
  text: string;
  onChange: React.Dispatch<React.SetStateAction<string>>;
}): React.JSX.Element {
  const task = useAssistantTask<Review>('llm.script_review');
  return (
    <>
      <AssistantButton
        label={t('llm.button.review')}
        busy={task.busy}
        error={task.error}
        disabled={!text.trim()}
        onClick={() => task.run({ text })}
      />
      {task.result ? (
        <ScriptReviewDiff
          key={task.jobId}
          paragraphs={task.result.paragraphs}
          discarded={task.result.discarded.length}
          onAccept={(paragraph) => onChange((current) => replaceParagraph(current, paragraph))}
        />
      ) : null}
    </>
  );
}
