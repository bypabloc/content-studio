import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { SendToActions } from '@/shared/navigation/SendToActions';
import { t } from '@/shared/i18n/t';

afterEach(() => {
  cleanup();
  window.location.hash = '';
});

describe('SendToActions', () => {
  it('muestra los destinos de audio y envía la ruta a Normalizar', () => {
    render(<SendToActions path="D:/media/voice.wav" type="audio" />);
    const group = screen.getByRole('group', { name: t('editor.send_to') });

    expect(within(group).getAllByRole('button')).toHaveLength(4);
    fireEvent.click(within(group).getByRole('button', { name: t('normalize.submit') }));

    expect(window.location.hash).toBe('#/normalize?path=D%3A%2Fmedia%2Fvoice.wav');
  });

  it('omite Normalizar para video', () => {
    render(<SendToActions path="D:/media/clip.mp4" type="video" />);
    const group = screen.getByRole('group', { name: t('editor.send_to') });

    expect(within(group).getAllByRole('button')).toHaveLength(3);
    expect(within(group).queryByRole('button', { name: t('normalize.submit') })).toBeNull();
  });
});
