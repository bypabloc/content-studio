import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MicrophonePicker } from '@/features/recording/MicrophonePicker';
import { listMicrophones } from '@/features/recording/microphones';
import { t } from '@/shared/i18n/t';

vi.mock('@/features/recording/microphones', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/features/recording/microphones')>();
  return { ...actual, listMicrophones: vi.fn() };
});

function device(deviceId: string, label: string): MediaDeviceInfo {
  return { kind: 'audioinput', deviceId, label, groupId: 'grupo', toJSON: () => ({}) } as MediaDeviceInfo;
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('MicrophonePicker (spec 010, D-2)', () => {
  it('no lista nada hasta que se pide: muestra el botón para ver los micrófonos', () => {
    render(<MicrophonePicker value="" onChange={vi.fn()} />);

    expect(screen.getByRole('button', { name: t('voices.mic.show') })).toBeTruthy();
    expect(screen.queryByRole('combobox', { name: t('voices.mic.label') })).toBeNull();
  });

  it('al pedirlos muestra cada micrófono, y elegir uno lo entrega', async () => {
    vi.mocked(listMicrophones).mockResolvedValue([device('mic-1', 'HyperX'), device('mic-2', 'Realtek')]);
    const onChange = vi.fn();
    render(<MicrophonePicker value="" onChange={onChange} />);

    fireEvent.click(screen.getByRole('button', { name: t('voices.mic.show') }));
    await userEvent.click(await screen.findByRole('combobox', { name: t('voices.mic.label') }));
    await userEvent.click(await screen.findByRole('option', { name: 'Realtek' }));

    expect(onChange).toHaveBeenCalledWith('mic-2');
  });

  it('si el sistema no da la lista, lo dice con su texto del catálogo', async () => {
    vi.mocked(listMicrophones).mockRejectedValue(new Error('NotAllowedError'));
    render(<MicrophonePicker value="" onChange={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: t('voices.mic.show') }));

    expect(await screen.findByText(t('voices.mic.error'))).toBeTruthy();
  });

  it('un micrófono sin nombre se muestra como Micrófono con su número', async () => {
    vi.mocked(listMicrophones).mockResolvedValue([device('mic-1', 'HyperX'), device('mic-2', '')]);
    render(<MicrophonePicker value="" onChange={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: t('voices.mic.show') }));
    await userEvent.click(await screen.findByRole('combobox', { name: t('voices.mic.label') }));

    expect(await screen.findByRole('option', { name: t('voices.mic.unnamed', { n: 2 }) })).toBeTruthy();
  });

  it('con registro, anota la lista de micrófonos que salió', async () => {
    vi.mocked(listMicrophones).mockResolvedValue([device('mic-1', 'HyperX')]);
    const log = vi.fn();
    render(<MicrophonePicker value="" onChange={vi.fn()} log={log} />);

    fireEvent.click(screen.getByRole('button', { name: t('voices.mic.show') }));

    await waitFor(() => expect(log).toHaveBeenCalledWith('mic.list', { devices: ['HyperX'] }));
  });

  it('con registro, anota el fallo con el nombre del error', async () => {
    const failure = new Error('no abre');
    failure.name = 'NotAllowedError';
    vi.mocked(listMicrophones).mockRejectedValue(failure);
    const log = vi.fn();
    render(<MicrophonePicker value="" onChange={vi.fn()} log={log} />);

    fireEvent.click(screen.getByRole('button', { name: t('voices.mic.show') }));

    await waitFor(() => expect(log).toHaveBeenCalledWith('mic.list.error', { name: 'NotAllowedError' }));
  });
});
