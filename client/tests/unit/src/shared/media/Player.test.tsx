import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import WaveSurfer from 'wavesurfer.js';
import { Player } from '@/shared/media/Player';
import { t } from '@/shared/i18n/t';

// wavesurfer.js dibuja con canvas y reproduce con el audio del WebView: el test lo cambia por un doble por pista, que
// anota sus llamadas y deja disparar sus eventos.
const { makeWave } = vi.hoisted(() => {
  function createWave() {
    const handlers = new Map<string, () => void>();
    return {
      on: vi.fn((event: string, handler: () => void) => {
        handlers.set(event, handler);
      }),
      emit: (event: string) => handlers.get(event)?.(),
      playPause: vi.fn(() => Promise.resolve()),
      pause: vi.fn(),
      destroy: vi.fn(),
    };
  }
  return { makeWave: createWave };
});
vi.mock('wavesurfer.js', () => ({ default: { create: vi.fn(() => makeWave()) } }));

/** La última pista creada por el reproductor de la prueba. */
function lastWave() {
  return vi.mocked(WaveSurfer.create).mock.results.at(-1)?.value as ReturnType<typeof makeWave>;
}

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

    fireEvent.pointerDown(screen.getByRole('button'));
    fireEvent.keyDown(window, { key: ' ' });
    fireEvent.keyDown(window, { key: ' ' });

    expect(lastWave().playPause).toHaveBeenCalledTimes(2);
  });

  it('Espacio controla solo la pista que el usuario tocó, no todas las que hay en pantalla', () => {
    render(
      <>
        <Player src="/files?path=a.wav" peaks={[0.1]} />
        <Player src="/files?path=b.wav" peaks={[0.2]} />
      </>,
    );
    const [first, second] = vi.mocked(WaveSurfer.create).mock.results.map((result) => result.value) as ReturnType<
      typeof makeWave
    >[];

    fireEvent.pointerDown(screen.getAllByRole('button')[1]);
    fireEvent.keyDown(window, { key: ' ' });

    expect(second.playPause).toHaveBeenCalledTimes(1);
    expect(first.playPause).not.toHaveBeenCalled();
  });

  it('Espacio sin ninguna pista tocada no reproduce', () => {
    render(<Player src="/files?path=a.wav" peaks={[0.1]} />);

    fireEvent.keyDown(window, { key: ' ' });

    expect(lastWave().playPause).not.toHaveBeenCalled();
  });

  it('Espacio escrito en un campo de texto no reproduce', () => {
    render(
      <>
        <Player src="/files?path=a.wav" peaks={[0.1]} />
        <input aria-label="nota" />
      </>,
    );

    fireEvent.keyDown(screen.getByRole('textbox', { name: 'nota' }), { key: ' ' });

    expect(lastWave().playPause).not.toHaveBeenCalled();
  });

  it('el botón dice Pausar mientras suena y Reproducir al parar', () => {
    render(<Player src="/files?path=a.wav" peaks={[0.1]} />);

    expect(screen.getByRole('button', { name: t('player.play') })).toBeTruthy();
    act(() => lastWave().emit('play'));
    expect(screen.getByRole('button', { name: t('player.pause') })).toBeTruthy();
    act(() => lastWave().emit('pause'));
    expect(screen.getByRole('button', { name: t('player.play') })).toBeTruthy();
  });

  it('el botón reproduce o pausa, y al desmontar libera la forma de onda', () => {
    const { unmount } = render(<Player src="/files?path=a.wav" peaks={[0.1]} />);
    const wave = lastWave();

    fireEvent.click(screen.getByRole('button', { name: t('player.play') }));
    expect(wave.playPause).toHaveBeenCalledTimes(1);
    unmount();
    expect(wave.destroy).toHaveBeenCalledTimes(1);
  });

  it('al empezar una pista, las demás se pausan (Comparar)', () => {
    render(
      <>
        <Player src="/files?path=a.wav" peaks={[0.1]} />
        <Player src="/files?path=b.wav" peaks={[0.2]} />
      </>,
    );
    const [first, second] = vi.mocked(WaveSurfer.create).mock.results.map((result) => result.value);

    act(() => (first as ReturnType<typeof makeWave>).emit('play'));

    expect((second as ReturnType<typeof makeWave>).pause).toHaveBeenCalledTimes(1);
    expect((first as ReturnType<typeof makeWave>).pause).not.toHaveBeenCalled();
  });
});
