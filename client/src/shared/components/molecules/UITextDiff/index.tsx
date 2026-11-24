import { UIDiffText } from '../../atoms/UIDiffText';
import { UIText } from '../../atoms/UIText';

type Part = { same: string } | { removed: string; added: string };

/**
 * Diferencia por palabras (LCS): las palabras iguales quedan tal cual y cada tramo distinto se muestra tachado y
 * agregado. Pura, para probarla y para que la usen el guion y los subtítulos.
 */
export function wordDiff(before: string, after: string): Part[] {
  const a = before.split(/\s+/).filter(Boolean);
  const b = after.split(/\s+/).filter(Boolean);
  const lcs = Array.from({ length: a.length + 1 }, () => new Array<number>(b.length + 1).fill(0));
  for (let i = a.length - 1; i >= 0; i -= 1) {
    for (let j = b.length - 1; j >= 0; j -= 1) {
      lcs[i][j] = a[i] === b[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1]);
    }
  }
  const parts: Part[] = [];
  let removed: string[] = [];
  let added: string[] = [];
  const flush = () => {
    if (removed.length || added.length) parts.push({ removed: removed.join(' '), added: added.join(' ') });
    removed = [];
    added = [];
  };
  let i = 0;
  let j = 0;
  while (i < a.length || j < b.length) {
    if (i < a.length && j < b.length && a[i] === b[j]) {
      flush();
      parts.push({ same: a[i] });
      i += 1;
      j += 1;
    } else if (j < b.length && (i === a.length || lcs[i][j + 1] >= lcs[i + 1][j])) {
      added.push(b[j]);
      j += 1;
    } else {
      removed.push(a[i]);
      i += 1;
    }
  }
  flush();
  return parts;
}

/** El texto anterior y el nuevo en una sola línea, con lo que cambia tachado y agregado. */
export function UITextDiff({ before, after }: { before: string; after: string }): React.JSX.Element {
  return (
    <UIText variant="body">
      {wordDiff(before, after).map((part, index) =>
        'same' in part ? `${part.same} ` : <UIDiffText key={index} label="" expected={part.removed} said={part.added} />,
      )}
    </UIText>
  );
}
