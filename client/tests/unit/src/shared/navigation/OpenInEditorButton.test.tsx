import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { OpenInEditorButton } from '@/shared/navigation/OpenInEditorButton';
import { t } from '@/shared/i18n/t';

afterEach(() => {
  cleanup();
  window.location.hash = '';
});

describe('OpenInEditorButton', () => {
  it('se deshabilita si no recibe rutas', () => {
    render(<OpenInEditorButton paths={[]} />);

    expect(screen.getByRole('button', { name: t('action.open_editor') }).hasAttribute('disabled')).toBe(true);
  });

  it('abre en el Editor las rutas válidas', () => {
    render(<OpenInEditorButton paths={['', 'D:/media/voice.wav']} />);

    fireEvent.click(screen.getByRole('button', { name: t('action.open_editor') }));

    expect(new URLSearchParams(window.location.hash.split('?')[1]).getAll('add')).toEqual(['D:/media/voice.wav']);
  });
});
