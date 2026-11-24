import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { CueSuggestions } from '@/features/subtitles/CueSuggestions';
import { t } from '@/shared/i18n/t';

afterEach(cleanup);

const rows = [
  { id: 1, content: 'Hola Klinikae' },
  { id: 2, content: 'todo muy bien', flag: 'review', checked: false },
];

describe('CueSuggestions (spec 021, D-5)', () => {
  it('WHEN se eligen cues THEN aplica solo esos; los marcados para revisar empiezan sin elegir', () => {
    const onApply = vi.fn();
    render(<CueSuggestions title="Corregir" rows={rows} busy={false} onApply={onApply} />);

    expect(screen.getByText(t('llm.subtitles.flag.review'))).toBeTruthy();
    const second = screen.getByRole('checkbox', { name: t('llm.subtitles.cue', { id: 2 }) }) as HTMLInputElement;
    expect(second.checked).toBe(false);
    fireEvent.click(screen.getByRole('checkbox', { name: t('llm.subtitles.cue', { id: 1 }) }));
    expect(screen.getByRole('button', { name: t('llm.apply_selected') }).hasAttribute('disabled')).toBe(true);
    fireEvent.click(second);
    fireEvent.click(screen.getByRole('button', { name: t('llm.apply_selected') }));
    fireEvent.click(screen.getByRole('button', { name: t('llm.accept_all') }));

    expect(onApply.mock.calls).toEqual([[[2]], [[1, 2]]]);
  });

  it('WHEN no es por cue THEN se acepta la pista entera', () => {
    const onApply = vi.fn();
    render(<CueSuggestions title="Traducir" rows={rows} selectable={false} busy={false} onApply={onApply} />);

    expect(screen.queryByRole('checkbox')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: t('llm.subtitles.accept_track') }));

    expect(onApply).toHaveBeenCalledWith(null);
  });
});
