import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ClipMissing } from '@/features/editor/browser/ClipMissing';
import { t } from '@/shared/i18n/t';

const { open } = vi.hoisted(() => ({ open: vi.fn() }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }));

const OLD_SOURCE = 'D:\\Media\\voz-movida.wav';
const NEW_SOURCE = 'D:\\Media\\voz-correcta.wav';

afterEach(cleanup);

describe('ClipMissing', () => {
  beforeEach(() => open.mockReset());

  it('permite buscar una ruta nueva y la comunica para todas las instancias', async () => {
    const onRelink = vi.fn();
    open.mockResolvedValue(NEW_SOURCE);
    render(<ClipMissing src={OLD_SOURCE} onRelink={onRelink} />);

    fireEvent.click(screen.getByRole('button', { name: t('editor.clip.find') }));

    expect(open).toHaveBeenCalledOnce();
    await waitFor(() => expect(onRelink).toHaveBeenCalled());
    expect(onRelink).toHaveBeenCalledWith(OLD_SOURCE, NEW_SOURCE);
  });

  it('no cambia la fuente si se cancela el diálogo', async () => {
    const onRelink = vi.fn();
    open.mockResolvedValue(null);
    render(<ClipMissing src="missing.wav" onRelink={onRelink} />);

    fireEvent.click(screen.getByRole('button', { name: t('editor.clip.find') }));

    await screen.findByText(t('editor.clip.missing', { source: 'missing.wav' }));
    expect(onRelink).not.toHaveBeenCalled();
  });

  it('muestra un error localizado si no puede abrir el diálogo', async () => {
    open.mockImplementationOnce(() => Promise.reject('dialog failed'));
    render(<ClipMissing src={OLD_SOURCE} onRelink={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: t('editor.clip.find') }));

    expect(await screen.findByText(t('editor.clip.relink_error'))).toBeTruthy();
  });
});
