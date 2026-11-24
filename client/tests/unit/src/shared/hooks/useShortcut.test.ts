import { renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useShortcut } from '@/shared/hooks/useShortcut';

function press(init: KeyboardEventInit) {
  window.dispatchEvent(new KeyboardEvent('keydown', init));
}

describe('useShortcut', () => {
  it('mod+k responde a Ctrl o Meta con la tecla k, y a nada más', () => {
    const handler = vi.fn();
    renderHook(() => useShortcut('mod+k', handler));

    press({ key: 'k', ctrlKey: true });
    press({ key: 'k', metaKey: true });
    press({ key: 'j', ctrlKey: true });
    press({ key: 'k' });

    expect(handler).toHaveBeenCalledTimes(2);
  });

  it('mod+enter no responde con Shift+Enter', () => {
    const handler = vi.fn();
    renderHook(() => useShortcut('mod+enter', handler));

    press({ key: 'Enter', ctrlKey: true, shiftKey: true });
    press({ key: 'Enter', ctrlKey: true });

    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('al desmontar deja de escuchar', () => {
    const handler = vi.fn();
    const { unmount } = renderHook(() => useShortcut('mod+k', handler));

    unmount();
    press({ key: 'k', ctrlKey: true });

    expect(handler).not.toHaveBeenCalled();
  });
});
