import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { EngineCard, type EngineAction } from '@/features/engines/EngineCard';

const qwen = {
  engine: 'qwen-0.6b',
  family: 'narration',
  size_gb: 7,
  vram_gb: 3.2,
  cpu: false,
  license: 'Apache-2.0',
  commercial: true,
  status: 'installed',
  owner: 'app',
  size_bytes: 7_000_000_000,
  job_id: null,
  verification: { ok: true, checked_at: '2026-11-21T00:00:00Z', duration_s: 1 },
};

const gpu = { name: 'RTX 4060 Laptop GPU', vram_gb: 8, driver: '1', cuda: '12.8' };

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('EngineCard', () => {
  it('muestra estado, licencia, VRAM y acciones de un motor instalado', () => {
    render(<EngineCard engine={qwen} gpu={gpu} onAction={vi.fn()} />);

    expect(screen.getByRole('region', { name: 'qwen-0.6b' })).toBeTruthy();
    expect(screen.getByText('Apache-2.0')).toBeTruthy();
    expect(screen.getByText(/Entra/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Verificar' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Reparar' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Desinstalar' })).toBeTruthy();
  });

  it('AC-7: un motor con otra receta muestra la actualización y Actualizar reinstala', () => {
    const onAction = vi.fn();
    render(<EngineCard engine={{ ...qwen, status: 'outdated' }} gpu={gpu} onAction={onAction} />);

    expect(screen.getByText('Actualización disponible')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Verificar' })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar' }));
    expect(onAction).toHaveBeenCalledWith({ type: 'install', engine: 'qwen-0.6b' });
  });

  it('permite instalar con poca VRAM y muestra la advertencia', () => {
    render(
      <EngineCard
        engine={{ ...qwen, status: 'missing', owner: null, verification: null }}
        gpu={{ ...gpu, vram_gb: 2 }}
        onAction={vi.fn()}
      />,
    );

    expect(screen.getByText(/No entra/)).toBeTruthy();
    expect((screen.getByRole('button', { name: 'Instalar' }) as HTMLButtonElement).disabled).toBe(false);
  });

  it('clasifica como justa la VRAM entre el requisito y el margen del 25 %', () => {
    render(
      <EngineCard
        engine={{ ...qwen, status: 'missing', owner: null, verification: null }}
        gpu={{ ...gpu, vram_gb: 3.5 }}
        onAction={vi.fn()}
      />,
    );

    expect(screen.getByText(/Justo/)).toBeTruthy();
    expect((screen.getByRole('button', { name: 'Instalar' }) as HTMLButtonElement).disabled).toBe(false);
  });

  it('muestra el tamaño real en KB y MB cuando el motor ya ocupa disco', () => {
    render(<EngineCard engine={{ ...qwen, size_bytes: 5_000_000 }} gpu={gpu} onAction={vi.fn()} />);
    expect(screen.getByText('En disco: 5 MB')).toBeTruthy();

    cleanup();
    render(<EngineCard engine={{ ...qwen, size_bytes: 5_000 }} gpu={gpu} onAction={vi.fn()} />);
    expect(screen.getByText('En disco: 5 KB')).toBeTruthy();
  });

  it('deshabilita la instalación sin GPU cuando el motor no admite CPU', () => {
    render(
      <EngineCard
        engine={{ ...qwen, status: 'missing', owner: null, verification: null }}
        gpu={null}
        onAction={vi.fn()}
      />,
    );

    expect((screen.getByRole('button', { name: 'Instalar' }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText('Requiere GPU')).toBeTruthy();
  });

  it('exige escribir el nombre exacto para desinstalar un motor externo', () => {
    const onAction = vi.fn<(action: EngineAction) => void>();
    render(
      <EngineCard
        engine={{ ...qwen, status: 'external', owner: 'external' }}
        gpu={gpu}
        onAction={onAction}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Desinstalar' }));
    const name = screen.getByRole('textbox', { name: 'Escribe el nombre del motor' });
    const confirm = screen.getByRole('button', { name: 'Confirmar desinstalación' }) as HTMLButtonElement;
    expect(confirm.disabled).toBe(true);
    fireEvent.change(name, { target: { value: 'QWEN-0.6B' } });
    expect(confirm.disabled).toBe(true);
    fireEvent.change(name, { target: { value: 'qwen-0.6b' } });
    expect(confirm.disabled).toBe(false);
    fireEvent.click(confirm);

    expect(onAction).toHaveBeenCalledWith({ type: 'uninstall', engine: 'qwen-0.6b', force: true });
  });

  it('muestra la reparación de un motor dañado y la última verificación fallida', () => {
    render(
      <EngineCard
        engine={{ ...qwen, status: 'broken', owner: 'app', verification: { ok: false } }}
        gpu={gpu}
        onAction={vi.fn()}
      />,
    );

    expect(screen.getByText('La última verificación falló.')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Reparar' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Instalar' })).toBeNull();
  });

  it('pide confirmar la desinstalación administrada y la cancela si se rechaza', () => {
    const onAction = vi.fn<(action: EngineAction) => void>();
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    render(<EngineCard engine={qwen} gpu={gpu} onAction={onAction} />);

    fireEvent.click(screen.getByRole('button', { name: 'Desinstalar' }));

    expect(window.confirm).toHaveBeenCalledWith(expect.stringContaining('7 GB'));
    expect(onAction).not.toHaveBeenCalled();
  });
});
