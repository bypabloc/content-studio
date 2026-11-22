import { act, cleanup, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useFilePaths } from '@/shared/hooks/useFilePaths';

const { open, drag } = vi.hoisted(() => ({
  open: vi.fn(),
  drag: { handler: null as null | ((event: { payload: unknown }) => void) },
}));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }));
vi.mock('@tauri-apps/api/webview', () => ({
  getCurrentWebview: () => ({
    onDragDropEvent: (handler: (event: { payload: unknown }) => void) => {
      drag.handler = handler;
      return Promise.resolve(() => {});
    },
  }),
}));

const inTauri = window as unknown as Record<string, unknown>;

function setup() {
  const onPaths = vi.fn();
  const onRejected = vi.fn();
  const hook = renderHook(() => useFilePaths({ extensions: ['mp4', 'wav'], onPaths, onRejected }));
  return { hook, onPaths, onRejected };
}

describe('useFilePaths', () => {
  beforeEach(() => {
    inTauri.__TAURI_INTERNALS__ = {};
    open.mockReset();
    drag.handler = null;
  });
  afterEach(() => {
    delete inTauri.__TAURI_INTERNALS__;
    cleanup();
  });

  it('entrega las rutas soltadas con una extensión de la lista y avisa de las que no lo son', async () => {
    const { onPaths, onRejected } = setup();

    await act(async () => {
      drag.handler?.({ payload: { type: 'drop', paths: ['/media/a.mp4', '/media/notas.txt', '/media/b.WAV'] } });
    });

    expect(onPaths).toHaveBeenCalledWith(['/media/a.mp4', '/media/b.WAV']);
    expect(onRejected).toHaveBeenCalledWith(['/media/notas.txt']);
  });

  it('marca el arrastre sobre la ventana y lo quita al soltar', async () => {
    const { hook } = setup();

    await act(async () => drag.handler?.({ payload: { type: 'enter', paths: [] } }));
    expect(hook.result.current.dragging).toBe(true);

    await act(async () => drag.handler?.({ payload: { type: 'drop', paths: [] } }));
    expect(hook.result.current.dragging).toBe(false);
  });

  it('elige con el diálogo del sistema, con varios archivos a la vez', async () => {
    open.mockResolvedValue(['/media/a.mp4']);
    const { hook, onPaths } = setup();

    await act(async () => hook.result.current.pick());

    expect(open).toHaveBeenCalledWith(expect.objectContaining({ multiple: true }));
    expect(onPaths).toHaveBeenCalledWith(['/media/a.mp4']);
  });

  it('fuera de Tauri no abre el diálogo ni escucha el arrastre', async () => {
    delete inTauri.__TAURI_INTERNALS__;
    const { hook } = setup();

    await act(async () => hook.result.current.pick());

    expect(open).not.toHaveBeenCalled();
    expect(drag.handler).toBeNull();
  });
});
