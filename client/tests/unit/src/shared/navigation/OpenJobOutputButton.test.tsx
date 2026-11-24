import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { OpenJobOutputButton } from '@/shared/navigation/OpenJobOutputButton';
import { t } from '@/shared/i18n/t';

const { api, toastError } = vi.hoisted(() => ({
  api: { get: vi.fn() },
  toastError: vi.fn(),
}));

vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@/shared/components/molecules/UIToast', () => ({ toast: { error: toastError } }));

beforeEach(() => {
  window.location.hash = '';
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  window.location.hash = '';
});

describe('OpenJobOutputButton', () => {
  it('deshabilita el acceso cuando no hay una carpeta de salida', () => {
    render(<OpenJobOutputButton outputDir={null} />);

    expect(screen.getByRole('button', { name: t('action.open_editor') }).hasAttribute('disabled')).toBe(true);
    expect(api.get).not.toHaveBeenCalled();
  });

  it('abre en el Editor solo los archivos de audio y video de la salida', async () => {
    api.get.mockResolvedValue({
      entries: [
        { kind: 'audio', path: 'out/job/take one.wav' },
        { kind: 'video', path: 'out/job/render.mp4' },
        { kind: 'image', path: 'out/job/cover.png' },
      ],
    });
    render(<OpenJobOutputButton outputDir="out/job" />);

    fireEvent.click(screen.getByRole('button', { name: t('action.open_editor') }));

    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/fs/list?path=out%2Fjob&kinds=audio%2Cvideo'));
    await waitFor(() => {
      const query = new URLSearchParams(window.location.hash.split('?')[1]);
      expect(query.getAll('add')).toEqual(['out/job/take one.wav', 'out/job/render.mp4']);
    });
  });

  it('no abre el Editor si la salida no contiene medios compatibles', async () => {
    api.get.mockResolvedValue({ entries: [{ kind: 'image', path: 'out/job/cover.png' }] });
    render(<OpenJobOutputButton outputDir="out/job" />);

    fireEvent.click(screen.getByRole('button', { name: t('action.open_editor') }));

    await waitFor(() => expect(api.get).toHaveBeenCalled());
    expect(window.location.hash).toBe('');
  });

  it('muestra un error si no puede listar la salida', async () => {
    api.get.mockRejectedValue(new Error('offline'));
    render(<OpenJobOutputButton outputDir="out/job" />);

    fireEvent.click(screen.getByRole('button', { name: t('action.open_editor') }));

    await waitFor(() => expect(toastError).toHaveBeenCalledWith(t('editor.import.error')));
    expect(window.location.hash).toBe('');
  });
});
