import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { type ReviewedParagraph, ScriptReviewDiff } from '@/features/narration/ScriptReviewDiff';
import { t } from '@/shared/i18n/t';

afterEach(cleanup);

const first: ReviewedParagraph = {
  index: 0,
  original: 'Tienes 24 horas; es DEMO.',
  revised: 'Tienes veinticuatro horas. Es demo.',
  changes: [{ rule: 13, before: '24', after: 'veinticuatro' }],
};
const second: ReviewedParagraph = { index: 1, original: 'Uno; dos.', revised: 'Uno. Dos.', changes: [] };

describe('ScriptReviewDiff (spec 021, AC-9)', () => {
  it('WHEN se acepta un párrafo y se descarta otro THEN solo el aceptado llega al editor', () => {
    const onAccept = vi.fn();
    render(<ScriptReviewDiff paragraphs={[first, second]} discarded={1} onAccept={onAccept} />);

    expect(screen.getByText(t('llm.review.rule', { rule: 13, before: '24', after: 'veinticuatro' }))).toBeTruthy();
    expect(screen.getByText(t('llm.review.discarded', { count: 1 }))).toBeTruthy();
    fireEvent.click(screen.getAllByRole('button', { name: t('llm.accept') })[0]);
    fireEvent.click(screen.getByRole('button', { name: t('llm.discard') }));

    expect(onAccept).toHaveBeenCalledTimes(1);
    expect(onAccept).toHaveBeenCalledWith(first);
    expect(screen.getByText(t('llm.review.empty'))).toBeTruthy();
  });

  it('WHEN se pulsa Aceptar todo THEN acepta cada párrafo pendiente', () => {
    const onAccept = vi.fn();
    render(<ScriptReviewDiff paragraphs={[first, second]} discarded={0} onAccept={onAccept} />);

    fireEvent.click(screen.getByRole('button', { name: t('llm.accept_all') }));

    expect(onAccept.mock.calls.map(([paragraph]) => paragraph.index)).toEqual([0, 1]);
  });
});
