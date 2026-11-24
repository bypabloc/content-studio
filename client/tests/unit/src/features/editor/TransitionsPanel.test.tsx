import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { TransitionsPanel } from '@/features/editor/TransitionsPanel';
import { t } from '@/shared/i18n/t';

afterEach(cleanup);

describe('TransitionsPanel', () => {
  it('permite agregar por clic y arrastrar el tipo de transición al timeline', () => {
    const onAdd = vi.fn();
    render(<TransitionsPanel onAdd={onAdd} />);
    const fade = screen.getByRole('button', { name: t('editor.transitions.fade') });

    fireEvent.click(fade);
    const dataTransfer = { setData: vi.fn(), effectAllowed: '' };
    fireEvent.dragStart(fade, { dataTransfer });

    expect(onAdd).toHaveBeenCalledWith('fade');
    expect(dataTransfer.setData).toHaveBeenCalledWith('application/x-editor-transition', 'fade');
    expect(dataTransfer.effectAllowed).toBe('copy');
  });
});
