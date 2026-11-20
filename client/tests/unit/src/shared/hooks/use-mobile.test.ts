import { renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { useIsMobile } from '@/shared/hooks/use-mobile';

describe('useIsMobile', () => {
  afterEach(() => {
    window.innerWidth = 1024;
  });

  it('es móvil por debajo de 768 px', () => {
    window.innerWidth = 500;

    const { result } = renderHook(() => useIsMobile());

    expect(result.current).toBe(true);
  });

  it('no es móvil desde 768 px', () => {
    window.innerWidth = 768;

    const { result } = renderHook(() => useIsMobile());

    expect(result.current).toBe(false);
  });
});
