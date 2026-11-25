import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { WelcomeWizard } from '@/features/welcome/WelcomeWizard';

const { api } = vi.hoisted(() => ({ api: { post: vi.fn(), put: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
const { open } = vi.hoisted(() => ({ open: vi.fn() }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }));

const system = { ffmpeg: null, git: null, gpu: null };
const storage = {
  engines: 'C:/Studio/engines',
  outputs: 'C:/Studio/outputs',
  engines_used_bytes: 0,
  engines_free_bytes: 20_000_000_000,
  outputs_used_bytes: 0,
  outputs_free_bytes: 20_000_000_000,
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.restoreAllMocks();
  window.location.hash = '';
});

describe('WelcomeWizard', () => {
  it('no aparece si ya se completó el primer uso', () => {
    const { container } = render(<WelcomeWizard open={false} system={system} storage={storage} onComplete={vi.fn()} />);

    expect(container.firstChild).toBeNull();
  });

  it('muestra herramientas y GPU, y permite instalar ffmpeg', () => {
    render(<WelcomeWizard open system={system} storage={storage} onComplete={vi.fn()} />);

    expect(screen.getByRole('dialog', { name: 'Bienvenida a Content Studio' })).toBeTruthy();
    expect(screen.getByText('No se detectó una GPU')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Instalar FFmpeg' }));
    fireEvent.click(screen.getByRole('button', { name: 'Instalar Git' }));

    expect(api.post).toHaveBeenCalledWith('/system/tools/ffmpeg/install');
    expect(api.post).toHaveBeenCalledWith('/system/tools/git/install');
  });

  it('recorre las cuatro etapas, permite sumar motores y encola la selección', async () => {
    api.post.mockResolvedValue({ id: 9, status: 'queued' });
    const complete = vi.fn();
    const engines = [
      { engine: 'voxcpm2', family: 'narration', size_gb: 4.8, vram_gb: 5, cpu: false, license: 'Apache-2.0', commercial: true, status: 'missing', owner: null, gated: false, size_bytes: 0, job_id: null, verification: null },
      { engine: 'acestep', family: 'music', size_gb: 8, vram_gb: 8, cpu: false, license: 'MIT', commercial: true, status: 'missing', owner: null, gated: false, size_bytes: 0, job_id: null, verification: null },
      { engine: 'qwen-0.6b', family: 'narration', size_gb: 7, vram_gb: 3, cpu: false, license: 'Apache-2.0', commercial: true, status: 'missing', owner: null, gated: false, size_bytes: 0, job_id: null, verification: null },
    ];
    const detected = { ...system, ffmpeg: { path: 'ffmpeg.exe', version: '9.1' }, git: { path: 'git.exe', version: '2.47' }, gpu: { name: 'RTX 4060', vram_gb: 8, driver: '1', cuda: '12' } };
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(<WelcomeWizard open system={detected} storage={storage} engines={engines} onComplete={complete} />);

    expect(screen.getByText('GPU detectada: RTX 4060, 8 GB de VRAM.')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    open.mockResolvedValueOnce('D:/Studio/engines');
    fireEvent.click(screen.getByRole('button', { name: 'Cambiar carpeta de Motores' }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/storage/move', { target: 'engines', to: 'D:/Studio/engines' }));
    expect(screen.getByText('Traslado de Motores agregado a la cola.')).toBeTruthy();
    expect(screen.getByText('Motores: D:/Studio/engines')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'qwen-0.6b' }));
    expect(screen.getByText('Tamaño total estimado: 19.8 GB')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    fireEvent.click(screen.getByRole('button', { name: 'Agregar a la cola e ir a Narración' }));

    await waitFor(() => expect(complete).toHaveBeenCalledOnce());
    expect(api.post).toHaveBeenCalledWith('/engines/voxcpm2/install');
    expect(api.post).toHaveBeenCalledWith('/engines/acestep/install');
    expect(api.post).toHaveBeenCalledWith('/engines/qwen-0.6b/install');
    expect(window.location.hash).toBe('#/narration');
  });

  it('muestra el fallo al no poder encolar y deja abierta la bienvenida', async () => {
    const complete = vi.fn();
    api.post.mockRejectedValueOnce(new Error('offline'));
    const engines = [
      { engine: 'voxcpm2', family: 'narration', size_gb: 4.8, vram_gb: 5, cpu: false, license: 'Apache-2.0', commercial: true, status: 'missing', owner: null, gated: false, size_bytes: 0, job_id: null, verification: null },
    ];
    render(<WelcomeWizard open system={system} storage={storage} engines={engines} onComplete={complete} />);
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    fireEvent.click(screen.getByRole('button', { name: 'Agregar a la cola e ir a Narración' }));

    expect(await screen.findByText('No se pudieron agregar todos los motores a la cola. Revisa Motores e inténtalo de nuevo.')).toBeTruthy();
    expect(complete).not.toHaveBeenCalled();
  });
});
