import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useReducedMotion } from '@/shared/hooks/use-reduced-motion';

/** Una media query falsa que guarda el listener de `change` para dispararlo a mano. */
function fakeMedia(matches: boolean) {
  let listener: (() => void) | undefined;
  const mql = {
    matches,
    addEventListener: vi.fn((_: string, fn: () => void) => {
      listener = fn;
    }),
    removeEventListener: vi.fn(),
  };
  return {
    mql,
    change(next: boolean) {
      mql.matches = next;
      listener?.();
    },
  };
}

describe('useReducedMotion', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('devuelve true cuando el sistema pide menos movimiento', () => {
    const media = fakeMedia(true);
    vi.spyOn(window, 'matchMedia').mockReturnValue(media.mql as unknown as MediaQueryList);

    const { result } = renderHook(() => useReducedMotion());

    expect(result.current).toBe(true);
    expect(window.matchMedia).toHaveBeenCalledWith('(prefers-reduced-motion: reduce)');
  });

  it('sigue el cambio de la preferencia sin recargar', () => {
    const media = fakeMedia(false);
    vi.spyOn(window, 'matchMedia').mockReturnValue(media.mql as unknown as MediaQueryList);

    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(false);

    act(() => media.change(true));

    expect(result.current).toBe(true);
  });

  it('quita el listener al desmontar', () => {
    const media = fakeMedia(false);
    vi.spyOn(window, 'matchMedia').mockReturnValue(media.mql as unknown as MediaQueryList);

    const { unmount } = renderHook(() => useReducedMotion());
    unmount();

    expect(media.mql.removeEventListener).toHaveBeenCalledWith('change', expect.any(Function));
  });

  it('devuelve false sin matchMedia', () => {
    const original = window.matchMedia;
    (window as unknown as { matchMedia: unknown }).matchMedia = undefined;
    try {
      const { result } = renderHook(() => useReducedMotion());

      expect(result.current).toBe(false);
    } finally {
      window.matchMedia = original;
    }
  });
});
