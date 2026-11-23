import { renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useNativeDrop } from '@/features/editor/useNativeDrop';

const { state } = vi.hoisted(() => ({ state: { options: null as null | { extensions: string[]; onPaths: (paths: string[]) => void } } }));
vi.mock('@/shared/hooks/useFilePaths', () => ({
  useFilePaths: (options: { extensions: string[]; onPaths: (paths: string[]) => void }) => {
    state.options = options;
    return { dragging: true, pick: vi.fn() };
  },
}));

describe('useNativeDrop', () => {
  it('acepta los formatos de audio y video del editor y delega las rutas', () => {
    const onPaths = vi.fn();
    const { result } = renderHook(() => useNativeDrop(onPaths));

    expect(result.current.dragging).toBe(true);
    expect(state.options?.extensions).toContain('wav');
    expect(state.options?.extensions).toContain('mp4');
    state.options?.onPaths(['D:\\media\\voice.wav']);
    expect(onPaths).toHaveBeenCalledWith(['D:\\media\\voice.wav']);
  });
});
