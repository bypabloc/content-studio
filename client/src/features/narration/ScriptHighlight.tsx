import type { LintIssue } from './useScriptLint';

/** Lo que va detrás del campo: el mismo tipo de letra y de sangría, para que cada palabra caiga en su sitio. */
export const EDITOR_TEXT = 'p-3 font-sans text-base leading-7 whitespace-pre-wrap break-words';

/** Un trozo del texto: sin `message` va normal; con `message`, es un aviso del linter. */
export interface Segment {
  text: string;
  message?: string;
}

/**
 * Parte el texto en trozos según los avisos. Cada aviso trae línea y columna (1-based) y su largo. Un aviso que se
 * solapa con otro ya marcado se omite, y uno fuera del texto también: la respuesta pudo ser de un texto anterior.
 */
export function markSegments(text: string, issues: LintIssue[]): Segment[] {
  const lineStarts = [0];
  for (const line of text.split('\n')) lineStarts.push(lineStarts[lineStarts.length - 1] + line.length + 1);
  const spans = issues
    .map((issue) => {
      const start = Math.min((lineStarts[issue.line - 1] ?? text.length) + issue.col - 1, text.length);
      return { start, end: Math.min(start + issue.length, text.length), message: issue.message };
    })
    .sort((a, b) => a.start - b.start);

  const segments: Segment[] = [];
  let cursor = 0;
  for (const span of spans) {
    if (span.start < cursor || span.end <= span.start) continue;
    if (span.start > cursor) segments.push({ text: text.slice(cursor, span.start) });
    segments.push({ text: text.slice(span.start, span.end), message: span.message });
    cursor = span.end;
  }
  if (cursor < text.length || segments.length === 0) segments.push({ text: text.slice(cursor) });
  return segments;
}

const SPACE = ' ';

/** El texto debajo del campo, con los avisos subrayados. Va en `aria-hidden`: lo que se lee es el campo. */
export function ScriptHighlight({ text, issues }: { text: string; issues: LintIssue[] }) {
  return (
    <div
      aria-hidden="true"
      className={`${EDITOR_TEXT} pointer-events-none absolute inset-0 overflow-hidden text-transparent`}
    >
      {markSegments(text, issues).map((segment, index) =>
        segment.message === undefined ? (
          <span key={index}>{segment.text}</span>
        ) : (
          <mark
            key={index}
            title={segment.message}
            className="bg-transparent text-transparent underline decoration-destructive decoration-wavy underline-offset-4"
          >
            {segment.text}
          </mark>
        ),
      )}
      {text.endsWith('\n') ? SPACE : null}
    </div>
  );
}
