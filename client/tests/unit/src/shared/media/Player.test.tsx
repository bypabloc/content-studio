import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import WaveSurfer from 'wavesurfer.js';
import { Player } from '@/shared/media/Player';
import { t } from '@/shared/i18n/t';

// wavesurfer.js dibuja con canvas y reproduce con el audio del WebView: el test lo cambia por un doble que anota sus
// llamadas y deja disparar sus eventos.
const { wave } = vi.hoisted(() => {
  const handlers = new Map<string, () => void>();
  return {
    wave: {
      on: vi.fn((event: string, handler: () => void) => {
        handlers.set(event, handler);
      }),
      emit: (event: string) => handlers.get(event)?.(),
      playPause: vi.fn(() => Promise.resolve()),
      destroy: vi.fn(),
    },
  };
});
vi.mock('wavesurfer.js', () => ({ default: { create: vi.fn(() => wave) } }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('Player', () => {
  it('carga la forma de onda con los picos del server, sin decodificar el audio', () => {
    render(<Player src="/files?path=a.wav" peaks={[0.1, 0.5]} />);

    expect(WaveSurfer.create).toHaveBeenCalledWith(
      expect.objectContaining({ url: '/files?path=a.wav', peaks: [[0.1, 0.5]] }),
    );
  });

  it('Espacio reproduce y pausa', () => {
    render(<Player src="/files?path=a.wav" peaks={[0.1]} />);

    fireEvent.keyDown(window, { key: ' ' });
    fireEvent.keyDown(window, { key: ' ' });

    expect(wave.playPause).toHaveBeenCalledTimes(2);
  });

  it('Espacio escrito en un campo de texto no reproduce', () => {
    render(
      <>
        <Player src="/files?path=a.wav" peaks={[0.1]} />
        <input aria-label="nota" />
      </>,
    );

    fireEvent.keyDown(screen.getByRole('textbox', { name: 'nota' }), { key: ' ' });

    expect(wave.playPause).not.toHaveBeenCalled();
  });

  it('el botón dice Pausar mientras suena y Reproducir al parar', () => {
    render(<Player src="/files?path=a.wav" peaks={[0.1]} />);

    expect(screen.getByRole('button', { name: t('player.play') })).toBeTruthy();
    act(() => wave.emit('play'));
    expect(screen.getByRole('button', { name: t('player.pause') })).toBeTruthy();
    act(() => wave.emit('pause'));
    expect(screen.getByRole('button', { name: t('player.play') })).toBeTruthy();
  });

  it('el botón reproduce o pausa, y al desmontar libera la forma de onda', () => {
    const { unmount } = render(<Player src="/files?path=a.wav" peaks={[0.1]} />);

    fireEvent.click(screen.getByRole('button', { name: t('player.play') }));
    expect(wave.playPause).toHaveBeenCalledTimes(1);
    unmount();
    expect(wave.destroy).toHaveBeenCalledTimes(1);
  });
});
