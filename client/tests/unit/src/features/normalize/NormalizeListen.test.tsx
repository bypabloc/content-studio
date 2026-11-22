import { act, cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { NormalizeListen } from '@/features/normalize/NormalizeListen';
import type { Job } from '@/shared/api/events';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
    del: vi.fn(),
    fileUrl: (path: string) => `file://${path}`,
    queryUrl: (path: string) => `http://test${path}`,
  },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

function doneJob(input: string): Job {
  return {
    id: 1,
    kind: 'media.normalize',
    status: 'done',
    progress: 1,
    stage: null,
    output_dir: 'out/normalize/1',
    params: { input, preset: 'podcast', enhance: false },
    error_code: null,
    error_detail: null,
  } as unknown as Job;
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('NormalizeListen', () => {
  it('arranca en el original, con su botón marcado', () => {
    render(<NormalizeListen job={doneJob('/media/a.wav')} />);

    expect(document.querySelector('audio')?.getAttribute('src')).toBe('file:///media/a.wav');
    expect(screen.getByRole('button', { name: t('normalize.ab.original') }).getAttribute('aria-pressed')).toBe('true');
  });

  it('el conmutador cambia la fuente al normalizado, en la carpeta del trabajo', async () => {
    render(<NormalizeListen job={doneJob('/media/a.wav')} />);

    await userEvent.click(screen.getByRole('button', { name: t('normalize.ab.normalized') }));

    expect(document.querySelector('audio')?.getAttribute('src')).toBe('file://out/normalize/1/normalized.wav');
    expect(screen.getByRole('button', { name: t('normalize.ab.normalized') }).getAttribute('aria-pressed')).toBe('true');
  });

  it('un video se escucha con un elemento de video, no de audio', () => {
    render(<NormalizeListen job={doneJob('/media/clip.mp4')} />);

    expect(document.querySelector('video')).not.toBeNull();
    expect(document.querySelector('audio')).toBeNull();
  });

  it('ofrece reproducir mientras está parado', () => {
    render(<NormalizeListen job={doneJob('/media/a.wav')} />);

    expect(screen.getByRole('button', { name: t('media.action.play') })).toBeTruthy();
  });

  it('el conmutador vuelve al original', async () => {
    render(<NormalizeListen job={doneJob('/media/a.wav')} />);

    await userEvent.click(screen.getByRole('button', { name: t('normalize.ab.normalized') }));
    await userEvent.click(screen.getByRole('button', { name: t('normalize.ab.original') }));

    expect(document.querySelector('audio')?.getAttribute('src')).toBe('file:///media/a.wav');
  });

  it('al cambiar de versión vuelve al mismo tiempo cuando la nueva carga', async () => {
    render(<NormalizeListen job={doneJob('/media/a.wav')} />);
    const audio = document.querySelector('audio') as HTMLAudioElement;
    let time = 7;
    Object.defineProperty(audio, 'currentTime', {
      configurable: true,
      get: () => time,
      set: (value: number) => {
        time = value;
      },
    });

    await userEvent.click(screen.getByRole('button', { name: t('normalize.ab.normalized') }));
    time = 0; // la fuente nueva empieza en cero
    act(() => {
      audio.dispatchEvent(new Event('loadedmetadata'));
    });

    expect(time).toBe(7);
  });

  it('el botón reproduce el medio y pasa a pausa mientras suena', async () => {
    const play = vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue(undefined);
    const pause = vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => {});
    render(<NormalizeListen job={doneJob('/media/a.wav')} />);
    const audio = document.querySelector('audio') as HTMLAudioElement;

    await userEvent.click(screen.getByRole('button', { name: t('media.action.play') }));
    expect(play).toHaveBeenCalled();

    act(() => {
      audio.dispatchEvent(new Event('play'));
    });
    Object.defineProperty(audio, 'paused', { configurable: true, get: () => false });
    await userEvent.click(await screen.findByRole('button', { name: t('media.action.pause') }));

    expect(pause).toHaveBeenCalled();
  });
});
