import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { useEditorAdd } from '@/features/editor/useEditorAdd';

describe('useEditorAdd', () => {
  it('lee varias rutas add y las consume sin borrar otros parámetros', () => {
    window.location.hash = '#/editor?path=project.json&add=C%3A%5CStudio%5Ca.wav&add=C%3A%5CStudio%5Cb.mp4';
    const { result } = renderHook(() => useEditorAdd());

    expect(result.current.paths).toEqual(['C:\\Studio\\a.wav', 'C:\\Studio\\b.mp4']);

    act(() => result.current.clear());

    expect(result.current.paths).toEqual([]);
    expect(window.location.hash).toBe('#/editor?path=project.json');
  });

  it('ignora rutas add vacías y limpia el hash cuando no quedan parámetros', () => {
    window.location.hash = '#/editor?add=&add=C%3A%5CStudio%5Ca.wav';
    const { result } = renderHook(() => useEditorAdd());

    expect(result.current.paths).toEqual(['C:\\Studio\\a.wav']);
    act(() => result.current.clear());
    expect(window.location.hash).toBe('#/editor');
  });
});
