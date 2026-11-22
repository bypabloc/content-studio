import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useSyncedMedia } from '@/shared/media/useSyncedMedia';

// Un medio falso: un EventTarget con tiempo, pausa y play/pause (jsdom no reproduce audio ni video).
function fakeMedia() {
  return Object.assign(new EventTarget(), {
    currentTime: 0,
    paused: true,
    play: vi.fn(async () => undefined),
    pause: vi.fn(),
  }) as unknown as HTMLMediaElement;
}

function emit(media: HTMLMediaElement, type: string, at?: number) {
  if (at !== undefined) media.currentTime = at;
  media.dispatchEvent(new Event(type));
}

describe('useSyncedMedia (spec 013, D-6)', () => {
  it('timeupdate del medio actualiza el tiempo que ve la pantalla', () => {
    const media = fakeMedia();
    const { result } = renderHook(() => useSyncedMedia(media));

    act(() => emit(media, 'timeupdate', 3.2));

    expect(result.current.time).toBe(3.2);
  });

  it('play y pause cambian si está sonando', () => {
    const media = fakeMedia();
    const { result } = renderHook(() => useSyncedMedia(media));

    act(() => emit(media, 'play'));
    expect(result.current.playing).toBe(true);
    act(() => emit(media, 'pause'));
    expect(result.current.playing).toBe(false);
  });

  it('seek mueve el medio y el tiempo', () => {
    const media = fakeMedia();
    const { result } = renderHook(() => useSyncedMedia(media));

    act(() => result.current.seek(7));

    expect(media.currentTime).toBe(7);
    expect(result.current.time).toBe(7);
  });

  it('toggle reproduce si está pausado y pausa si suena', () => {
    const media = fakeMedia();
    const { result } = renderHook(() => useSyncedMedia(media));

    act(() => result.current.toggle());
    expect(media.play).toHaveBeenCalledOnce();

    (media as { paused: boolean }).paused = false;
    act(() => result.current.toggle());
    expect(media.pause).toHaveBeenCalledOnce();
  });

  it('con skip, un tiempo dentro de un tramo cortado salta a su final (vista previa, sin cortes)', () => {
    const media = fakeMedia();
    const skip = (seconds: number) => (seconds >= 2 && seconds < 5 ? 5 : null);
    renderHook(() => useSyncedMedia(media, skip));

    act(() => emit(media, 'timeupdate', 3));

    expect(media.currentTime).toBe(5);
  });

  it('sin medio, seek y toggle no fallan y el tiempo no cambia', () => {
    const { result } = renderHook(() => useSyncedMedia(null));

    act(() => result.current.seek(1));
    act(() => result.current.toggle());

    expect(result.current.time).toBe(0);
    expect(result.current.playing).toBe(false);
  });

  it('al cambiar de medio deja de escuchar el anterior', () => {
    const first = fakeMedia();
    const second = fakeMedia();
    const { result, rerender } = renderHook(({ media }) => useSyncedMedia(media), { initialProps: { media: first } });

    rerender({ media: second });
    act(() => emit(first, 'timeupdate', 4));

    expect(result.current.time).toBe(0);
  });
});
