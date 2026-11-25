import { act, renderHook, waitFor } from '@testing-library/react';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useExternalRequests } from '@/app/external/useExternalRequests';
import { toast } from '@/shared/components/molecules/UIToast';
import { t } from '@/shared/i18n/t';
import { consumePrefill } from '@/shared/navigation/prefill';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn() }));
const { api } = vi.hoisted(() => ({ api: { post: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@tauri-apps/api/event', () => ({ listen: vi.fn() }));
vi.mock('@/shared/components/molecules/UIToast', () => ({ toast: { error: vi.fn(), info: vi.fn() } }));

const EXE = 'content-studio.exe';
let handler: ((event: { payload: string[] }) => Promise<void> | void) | undefined;

/** Simula el evento `external-request` que manda Rust cuando llega un segundo arranque (AC-5). */
async function emit(argv: string[]): Promise<void> {
  await waitFor(() => expect(handler).toBeDefined());
  await act(async () => {
    await handler?.({ payload: argv });
  });
}

describe('useExternalRequests (spec 031, F1 C3)', () => {
  beforeEach(() => {
    window.location.hash = '#/settings';
    handler = undefined;
    vi.clearAllMocks();
    vi.mocked(listen).mockImplementation(async (_name, callback) => {
      handler = callback as typeof handler;
      return () => {};
    });
    vi.mocked(invoke).mockImplementation((async (command: string) => (command === 'path_exists' ? true : [])) as never);
  });

  it('AC-1: WHEN la app arranca con un enlace open/music THEN abre Música', async () => {
    vi.mocked(invoke).mockResolvedValueOnce([EXE, 'content-studio://open/music']);
    renderHook(() => useExternalRequests());
    await waitFor(() => expect(window.location.hash).toBe('#/music'));
  });

  it('AC-1: WHEN llega open/music con la ventana abierta THEN la ventana va a Música', async () => {
    renderHook(() => useExternalRequests());
    await emit([EXE, 'content-studio://open/music']);
    expect(window.location.hash).toBe('#/music');
  });

  it('AC-3: WHEN llega new/narration THEN Narración queda rellenada y no se llama a la API', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch');
    renderHook(() => useExternalRequests());
    await emit([EXE, 'content-studio://new/narration?text=Hola&voice=yesid']);
    expect(window.location.hash).toBe('#/narration');
    expect(consumePrefill('narration')).toEqual({ text: 'Hola', voice: 'yesid' });
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });

  it('AC-3: WHEN llega media.convert con un archivo que existe THEN Conversor queda valores iniciales', async () => {
    renderHook(() => useExternalRequests());
    await emit([EXE, 'content-studio://new/media.convert?input=C%3A%5Cmedia%5Ca.wav&target=mp3']);
    expect(invoke).toHaveBeenCalledWith('path_exists', { path: 'C:\\media\\a.wav' });
    expect(consumePrefill('convert')).toEqual({ path: 'C:\\media\\a.wav', target: 'mp3' });
    expect(window.location.hash).toBe('#/convert');
  });

  it('AC-4: WHEN la ruta de media.convert no existe THEN avisa y no rellena', async () => {
    vi.mocked(invoke).mockImplementation((async (command: string) => (command === 'path_exists' ? false : [])) as never);
    renderHook(() => useExternalRequests());
    await emit([EXE, 'content-studio://new/media.convert?input=C%3A%5Cnope.wav']);
    expect(toast.error).toHaveBeenCalledWith(t('deeplink.invalid'));
    expect(consumePrefill('convert')).toBeUndefined();
    expect(window.location.hash).toBe('#/settings');
  });

  it('AC-4: WHEN la URL no es válida THEN avisa con deeplink.invalid y no navega', async () => {
    renderHook(() => useExternalRequests());
    await emit([EXE, 'content-studio://open/nope']);
    expect(toast.error).toHaveBeenCalledWith(t('deeplink.invalid'));
    expect(window.location.hash).toBe('#/settings');
  });

  it('AC-2: WHEN llega library/<id> THEN la biblioteca recibe el id para mostrar el detalle', async () => {
    renderHook(() => useExternalRequests());
    await emit([EXE, 'content-studio://library/7']);
    expect(window.location.hash).toBe('#/library');
    expect(consumePrefill('library')).toEqual({ id: '7' });
  });

  it('AC-2: WHEN llega job/<id> THEN la biblioteca recibe el trabajo', async () => {
    renderHook(() => useExternalRequests());
    await emit([EXE, 'content-studio://job/42']);
    expect(window.location.hash).toBe('#/library');
    expect(consumePrefill('library')).toEqual({ job: '42' });
  });

  it('AC-7: WHEN llegan tres archivos con convert-mp3 y uno no existe THEN encola dos trabajos y avisa de los dos', async () => {
    vi.mocked(invoke).mockImplementation((async (command: string, args?: { path?: string }) =>
      command === 'path_exists' ? args?.path !== 'no.wav' : []) as never);
    api.post.mockResolvedValue({ id: 1 });
    renderHook(() => useExternalRequests());
    await emit([EXE, '--send', 'convert-mp3', 'a.wav', 'b.wav', 'no.wav']);
    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(2));
    expect(api.post).toHaveBeenCalledWith('/jobs', { kind: 'media.convert', params: { input: 'a.wav', target: 'mp3', options: {} } });
    expect(toast.info).toHaveBeenCalledWith(t('sendto.queued', { count: '2' }));
    expect(toast.info).toHaveBeenCalledWith(t('sendto.skipped', { count: '1' }));
  });

  it.each([
    ['normalize', { kind: 'media.normalize', params: { input: 'a.wav', preset: 'youtube' } }],
    ['clean', { kind: 'clean.analyze', params: expect.objectContaining({ input: 'a.wav', auto_render: true }) }],
    ['transcribe', { kind: 'transcribe', params: { input: 'a.wav', model: 'large-v3-turbo', language: 'auto' } }],
  ])('AC-7: WHEN llega --send %s THEN encola ese trabajo con su valor por defecto', async (action, job) => {
    api.post.mockResolvedValue({ id: 1 });
    renderHook(() => useExternalRequests());
    await emit([EXE, '--send', action, 'a.wav']);
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/jobs', job));
  });

  it('AC-6: WHEN llega --send editor THEN abre el Editor con los archivos y no encola nada', async () => {
    renderHook(() => useExternalRequests());
    await emit([EXE, '--send', 'editor', 'a.wav']);
    await waitFor(() => expect(window.location.hash).toBe('#/editor?add=a.wav'));
    expect(api.post).not.toHaveBeenCalled();
  });
});
