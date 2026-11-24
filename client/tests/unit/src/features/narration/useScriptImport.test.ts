import { act, renderHook } from '@testing-library/react';
import { toast } from 'sonner';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { splitScriptPaths, useScriptImport } from '@/features/narration/useScriptImport';
import { t } from '@/shared/i18n/t';

const { open } = vi.hoisted(() => ({ open: vi.fn() }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }));

// El handler de arrastre que registra el hook: el test lo dispara a mano.
const { drop } = vi.hoisted(() => ({ drop: { handler: null as null | ((event: unknown) => void) } }));
vi.mock('@tauri-apps/api/webview', () => ({
  getCurrentWebview: () => ({
    onDragDropEvent: (handler: (event: unknown) => void) => {
      drop.handler = handler;
      return Promise.resolve(() => {});
    },
  }),
}));

vi.mock('sonner', () => ({ toast: { error: vi.fn() } }));

// El hook solo actúa dentro de la ventana de Tauri: el test finge estar en ella.
beforeEach(() => {
  vi.clearAllMocks();
  Object.assign(window, { __TAURI_INTERNALS__: {} });
});

afterEach(() => {
  Reflect.deleteProperty(window, '__TAURI_INTERNALS__');
});

describe('splitScriptPaths', () => {
  it('acepta .txt y .json sin importar las mayúsculas', () => {
    expect(splitScriptPaths(['C:/g/a.txt', 'C:/g/b.JSON', 'C:/g/D.Txt'])).toEqual({
      accepted: ['C:/g/a.txt', 'C:/g/b.JSON', 'C:/g/D.Txt'],
      rejected: [],
    });
  });

  it('rechaza lo demás, también lo que no tiene extensión', () => {
    expect(splitScriptPaths(['C:/g/guion.pdf', 'C:/g/notas.docx', 'C:/g/sin-extension'])).toEqual({
      accepted: [],
      rejected: ['C:/g/guion.pdf', 'C:/g/notas.docx', 'C:/g/sin-extension'],
    });
  });
});

describe('useScriptImport', () => {
  it('el diálogo pasa solo los guiones válidos y avisa de los demás', async () => {
    open.mockResolvedValue(['C:/g/a.txt', 'C:/g/x.pdf']);
    const onImport = vi.fn();
    const { result } = renderHook(() => useScriptImport(onImport));

    await act(() => result.current.pick());

    expect(open).toHaveBeenCalledWith(expect.objectContaining({ multiple: true }));
    expect(onImport).toHaveBeenCalledWith(['C:/g/a.txt']);
    expect(toast.error).toHaveBeenCalledWith(t('narration.import.rejected', { names: 'x.pdf' }));
  });

  it('cancelar el diálogo no importa nada', async () => {
    open.mockResolvedValue(null);
    const onImport = vi.fn();
    const { result } = renderHook(() => useScriptImport(onImport));

    await act(() => result.current.pick());

    expect(onImport).not.toHaveBeenCalled();
  });

  it('soltar archivos sobre la ventana importa los guiones válidos', async () => {
    const onImport = vi.fn();
    renderHook(() => useScriptImport(onImport));

    await act(async () => drop.handler?.({ payload: { type: 'drop', paths: ['C:/g/b.json'] } }));

    expect(onImport).toHaveBeenCalledWith(['C:/g/b.json']);
  });

  it('los demás eventos de arrastre (entrar, mover, salir) no importan', () => {
    const onImport = vi.fn();
    renderHook(() => useScriptImport(onImport));

    drop.handler?.({ payload: { type: 'over', position: { x: 0, y: 0 } } });

    expect(onImport).not.toHaveBeenCalled();
  });
});
