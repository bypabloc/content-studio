import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { RecordWizard } from '@/features/recording/RecordWizard';
import { t } from '@/shared/i18n/t';

const { api, recorder } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    upload: vi.fn(),
    fileUrl: (path: string) => `http://127.0.0.1:9000/files?path=${encodeURIComponent(path)}`,
  },
  recorder: { levels: { peak: -30, rms: -40 }, start: vi.fn(), stop: vi.fn() },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@/features/recording/capture/useRecorder', () => ({ useRecorder: () => recorder }));

vi.mock('@/shared/media/Player', async () => {
  const { createElement } = await import('react');
  return { Player: ({ src }: { src: string }) => createElement('p', null, `reproductor ${src}`) };
});

const KIT = {
  styles: [
    {
      style: 'neutral',
      optional: false,
      text: 'Hoy quiero contarte.',
      marked: 'Hoy quiero contarte. ↘',
      duration: { min: 10, max: 12 },
      ppm: 150,
    },
    {
      style: 'expert',
      optional: false,
      text: 'Mi método es simple.',
      marked: 'Mi método / es simple. ↘',
      duration: { min: 10, max: 12 },
      ppm: 150,
    },
  ],
};
const OK = { verdict: 'ok', reasons: [], notes: [], messages: [], measures: {} };
const RETAKE = { verdict: 'retake', reasons: ['edges'], notes: [], messages: [], measures: {} };

// Las tomas del estilo neutral y su chequeo: el test los cambia antes de grabar.
let takes: number[] = [];
let checks: Record<number, unknown> = {};
// El micrófono que está guardado en ajustes: vacío por defecto (el del sistema).
let savedMicrophone = '';

beforeEach(() => {
  takes = [];
  checks = {};
  savedMicrophone = '';
  recorder.start.mockReset().mockResolvedValue(undefined);
  recorder.stop.mockReset().mockResolvedValue(new Uint8Array([1, 2, 3]));
  api.get.mockImplementation(async (path: string) => {
    if (path === '/voices/kit') return KIT;
    if (path === '/voices/profiles/spec-010/takes/neutral') return { style: 'neutral', takes };
    if (path === '/voices/profiles/spec-010/takes/expert') return { style: 'expert', takes: [] };
    const detail = /\/takes\/neutral\/(\d+)$/.exec(path);
    if (detail) return { take: Number(detail[1]), path: `p${detail[1]}`, check: checks[Number(detail[1])] ?? null };
    if (path === '/settings/select.recording.microphone') return { key: 'select.recording.microphone', value: savedMicrophone };
    if (path.startsWith('/media/peaks')) return { peaks: [0.5] };
    return {};
  });
  api.upload.mockImplementation(async () => {
    takes = [...takes, 1];
    return { style: 'neutral', take: 1, job: 9 };
  });
  api.post.mockResolvedValue({});
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderWizard(): void {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <RecordWizard slug="spec-010" onDone={() => {}} />
    </QueryClientProvider>,
  );
}

describe('RecordWizard (spec 010, D-6)', () => {
  it('muestra el guion del primer estilo con su duración objetivo y su ritmo', async () => {
    renderWizard();

    expect(await screen.findByText('Hoy quiero contarte. ↘')).toBeTruthy();
    expect(screen.getByText(t('voices.record.step', { n: 1, total: 2 }))).toBeTruthy();
    expect(screen.getByText(t('voices.record.duration', { min: 10, max: 12 }))).toBeTruthy();
    expect(screen.getByText(t('voices.record.ppm', { ppm: 150 }))).toBeTruthy();
  });

  it('graba con el micrófono que se eligió y se guardó en ajustes', async () => {
    savedMicrophone = 'mic-1';
    renderWizard();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.start') }));

    await waitFor(() => expect(recorder.start).toHaveBeenCalledWith('mic-1'));
  });

  it('mientras el micrófono está abierto dice que está en uso, y al parar deja de decirlo', async () => {
    renderWizard();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.start') }));
    expect(await screen.findByText(t('voices.mic.in_use'))).toBeTruthy();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.stop') }));
    await waitFor(() => expect(screen.queryByText(t('voices.mic.in_use'))).toBeNull());
  });

  it('grabar y parar sube la toma como WAV y su veredicto aparece en la lista', async () => {
    checks[1] = OK;
    renderWizard();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.start') }));
    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.stop') }));

    await waitFor(() =>
      expect(api.upload).toHaveBeenCalledWith('/voices/profiles/spec-010/takes/neutral', new Uint8Array([1, 2, 3]), 'audio/wav'),
    );
    expect(await screen.findByText(t('voices.take.ok'), undefined, { timeout: 4000 })).toBeTruthy();
  });

  it('un chequeo que pide repetir dice la razón con su texto', async () => {
    checks[1] = RETAKE;
    renderWizard();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.start') }));
    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.stop') }));

    expect(await screen.findByText(t('voice.check.edges'), undefined, { timeout: 4000 })).toBeTruthy();
  });

  it('Siguiente pasa al estilo siguiente del kit', async () => {
    renderWizard();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.next') }));

    expect(await screen.findByText('Mi método / es simple. ↘')).toBeTruthy();
  });

  it('elegir una toma la manda a la referencia del estilo', async () => {
    takes = [1];
    checks[1] = OK;
    renderWizard();

    fireEvent.click(await screen.findByRole('button', { name: t('action.choose') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/voices/profiles/spec-010/takes/neutral/1/choose'));
  });

  it('sin permiso del micrófono avisa y no sube nada', async () => {
    recorder.start.mockRejectedValue(new Error('NotAllowedError'));
    renderWizard();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.start') }));

    expect(await screen.findByText(t('voices.record.error'))).toBeTruthy();
    expect(api.upload).not.toHaveBeenCalled();
  });

  it('la barra espaciadora graba y, al pulsarla de nuevo, para y sube', async () => {
    checks[1] = OK;
    renderWizard();
    await screen.findByText('Hoy quiero contarte. ↘');

    fireEvent.keyDown(window, { key: ' ' });
    await waitFor(() => expect(recorder.start).toHaveBeenCalledTimes(1));
    fireEvent.keyDown(window, { key: ' ' });

    await waitFor(() => expect(recorder.stop).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(api.upload).toHaveBeenCalledTimes(1));
  });

  it('Probar sala lleva el micrófono cinco segundos', async () => {
    renderWizard();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.room.start') }));

    await waitFor(() => expect(recorder.start).toHaveBeenCalledTimes(1));
  });

  it('Siguiente en el último estilo cierra el kit', async () => {
    renderWizard();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.next') }));
    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.next') }));

    expect(await screen.findByText(t('voices.record.finished'))).toBeTruthy();
  });

  it('si la subida falla, lo dice', async () => {
    api.upload.mockRejectedValue(new Error('sin red'));
    renderWizard();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.start') }));
    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.stop') }));

    expect(await screen.findByText(t('voices.record.upload_error'))).toBeTruthy();
  });

  it('la barra espaciadora escrita en un campo o en un botón no graba', async () => {
    renderWizard();
    const field = document.createElement('input');
    document.body.appendChild(field);

    fireEvent.keyDown(field, { key: ' ' });
    fireEvent.keyDown(await screen.findByRole('button', { name: t('voices.record.next') }), { key: ' ' });

    expect(recorder.start).not.toHaveBeenCalled();
    field.remove();
  });
});
