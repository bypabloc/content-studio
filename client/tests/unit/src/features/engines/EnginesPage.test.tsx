import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { EnginesPage } from '@/features/engines/EnginesPage';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), post: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const engines = [
  {
    engine: 'qwen-0.6b',
    family: 'narration',
    size_gb: 7,
    vram_gb: 3.2,
    cpu: false,
    license: 'Apache-2.0',
    commercial: true,
    status: 'missing',
    owner: null,
    size_bytes: 0,
    job_id: null,
    verification: null,
  },
  {
    engine: 'acestep', family: 'music', size_gb: 12, vram_gb: 8, cpu: false, license: 'MIT', commercial: true,
    status: 'installed', owner: 'app', size_bytes: 10, job_id: null, verification: { ok: false },
  },
  {
    engine: 'faster-whisper', family: 'transcription', size_gb: 4, vram_gb: 3, cpu: true, license: 'MIT', commercial: true,
    status: 'external', owner: 'external', size_bytes: 20, job_id: null, verification: { ok: true },
  },
];

function renderPage() {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <EnginesPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  api.get.mockImplementation(async (path: string) => {
    if (path === '/engines') return engines;
    if (path === '/system') return { ffmpeg: null, git: null, gpu: { name: 'RTX', vram_gb: 8, driver: '1', cuda: '12' } };
    return { id: 8, status: 'queued', progress: 0, stage: 'queued' };
  });
  api.post.mockResolvedValue({ id: 9, status: 'queued' });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.restoreAllMocks();
  window.location.hash = '';
});

describe('EnginesPage', () => {
  it('agrupa el catálogo y encola la instalación del motor seleccionado', async () => {
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByRole('heading', { name: 'Motores' })).toBeTruthy();
    expect(screen.getByText('Narración')).toBeTruthy();
    expect(screen.getByText('Música')).toBeTruthy();
    expect(screen.getByText('Transcripción')).toBeTruthy();
    expect(screen.getByRole('region', { name: 'qwen-0.6b' })).toBeTruthy();
    await user.click(screen.getByRole('button', { name: 'Instalar' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/engines/qwen-0.6b/install'));
  });

  it('envía verificar, reparar y desinstalar solo para rutas de motores administrados', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    const user = userEvent.setup();
    renderPage();
    const card = await screen.findByRole('region', { name: 'acestep' });

    await user.click(within(card).getByRole('button', { name: 'Verificar' }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/engines/acestep/verify'));
    await user.click(within(card).getByRole('button', { name: 'Reparar' }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/engines/acestep/install?repair=true'));
    await user.click(within(card).getByRole('button', { name: 'Desinstalar' }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/engines/acestep/uninstall'));
  });

  it('la confirmación externa exige el nombre y agrega force=true a la ruta', async () => {
    const user = userEvent.setup();
    renderPage();
    const card = await screen.findByRole('region', { name: 'faster-whisper' });
    await user.click(within(card).getByRole('button', { name: 'Desinstalar' }));
    const field = within(card).getByRole('textbox', { name: 'Escribe el nombre del motor' });
    await user.type(field, 'faster-whisper');
    await user.click(within(card).getByRole('button', { name: 'Confirmar desinstalación' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/engines/faster-whisper/uninstall?force=true'));
  });

  it('resalta el motor solicitado en el deep link y muestra error si falla la carga', async () => {
    const scroll = vi.fn();
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', { configurable: true, value: scroll });
    window.location.hash = '#/engines?engine=qwen-0.6b';
    renderPage();
    await screen.findByRole('region', { name: 'qwen-0.6b' });
    expect(scroll).toHaveBeenCalledWith({ block: 'center' });

    cleanup();
    api.get.mockRejectedValue(new Error('offline'));
    renderPage();
    expect(await screen.findByText('No se pudo cargar la lista de motores.')).toBeTruthy();
  });
});
