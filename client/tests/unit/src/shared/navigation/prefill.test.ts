import { act, cleanup, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { consumePrefill, setPrefill, usePrefillApply } from '@/shared/navigation/prefill';

afterEach(() => {
  cleanup();
  consumePrefill('demo');
});

describe('prefill (spec 031, AC-3)', () => {
  it('WHEN se deja un valores iniciales THEN la sección lo consume una sola vez', () => {
    setPrefill('demo', { text: 'Hola' });
    expect(consumePrefill('demo')).toEqual({ text: 'Hola' });
    expect(consumePrefill('demo')).toBeUndefined();
  });

  it('usePrefillApply aplica el valor al llegar, no lo repite y lo borra al salir de la sección', () => {
    const apply = vi.fn();
    const { rerender, unmount } = renderHook(() => usePrefillApply('demo', apply));
    expect(apply).not.toHaveBeenCalled();
    act(() => setPrefill('demo', { text: 'Hola' }));
    expect(apply).toHaveBeenCalledWith({ text: 'Hola' });
    rerender();
    expect(apply).toHaveBeenCalledTimes(1);
    unmount();
    expect(consumePrefill('demo')).toBeUndefined();
  });
});
