import { useState } from 'react';

import { UIButton } from '@/shared/components/atoms/UIButton';
import { UICard } from '@/shared/components/atoms/UICard';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UITextDiff } from '@/shared/components/molecules/UITextDiff';
import { t } from '@/shared/i18n/t';

export interface ReviewedParagraph {
  index: number;
  original: string;
  revised: string;
  changes: { rule: number; before: string; after: string }[];
}

interface Props {
  paragraphs: ReviewedParagraph[];
  discarded: number;
  onAccept: (paragraph: ReviewedParagraph) => void;
}

/**
 * Las sugerencias del asistente para el guion (spec 021, AC-9): un diff por párrafo con la regla de cada cambio, y
 * Aceptar o Descartar por párrafo o Aceptar todo. Lo que se descarta deja el texto como estaba.
 */
export function ScriptReviewDiff({ paragraphs, discarded, onAccept }: Props): React.JSX.Element {
  const [pending, setPending] = useState(paragraphs);
  const settle = (paragraph: ReviewedParagraph, accept: boolean) => {
    if (accept) onAccept(paragraph);
    setPending((current) => current.filter((item) => item.index !== paragraph.index));
  };
  return (
    <UIStack role="region" aria-label={t('llm.review.title')} gap="md">
      <UIText variant="subtitle">{t('llm.review.title')}</UIText>
      {pending.length === 0 ? <UIText variant="caption">{t('llm.review.empty')}</UIText> : null}
      {discarded > 0 ? <UIText variant="caption">{t('llm.review.discarded', { count: discarded })}</UIText> : null}
      {pending.map((paragraph) => (
        <UICard key={paragraph.index}>
          <UIStack gap="sm">
            <UITextDiff before={paragraph.original} after={paragraph.revised} />
            {paragraph.changes.map((change) => (
              <UIText key={`${change.rule}-${change.before}`} variant="caption">
                {t('llm.review.rule', { rule: change.rule, before: change.before, after: change.after })}
              </UIText>
            ))}
            <UIStack direction="row" gap="sm">
              <UIButton variant="primary" onClick={() => settle(paragraph, true)}>
                {t('llm.accept')}
              </UIButton>
              <UIButton variant="secondary" onClick={() => settle(paragraph, false)}>
                {t('llm.discard')}
              </UIButton>
            </UIStack>
          </UIStack>
        </UICard>
      ))}
      {pending.length > 1 ? (
        <UIButton variant="secondary" className="self-start" onClick={() => pending.forEach((paragraph) => settle(paragraph, true))}>
          {t('llm.accept_all')}
        </UIButton>
      ) : null}
    </UIStack>
  );
}
