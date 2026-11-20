import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ImportReference } from '@/features/recording/ImportReference';
import { ApiError } from '@/shared/api/errors';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({
  api: { get: vi.fn(), post: vi.fn(), upload: vi.fn(), fileUrl: (path: string) => path },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn() }));
// La onda necesita canvas: aquí es un botón que «mueve la región» a 2–12 s, con el tramo actual como texto.
vi.mock('@/features/recording/SpanPicker', async () => {
  const { createElement } = await import('react');
  return {
    SpanPicker: ({ start, end, onChange }: { start: number; end: number; onChange: (from: number, to: number) => void }) =>
      createElement('button', { type: 'button', 'data-testid': 'span-picker', onClick: () => onChange(2, 12) }, `${start}-${end}`),
  };
});

const KIT = {
  styles: [
    { style: 'neutral', optional: false, text: '', marked: '', duration: { min: 10, max: 12 }, ppm: 150 },
    { style: 'expert', optional: false, text: '', marked: '', duration: { min: 10, max: 12 }, ppm: 150 },
  ],
};

beforeEach(() => {
  api.get.mockImplementation(async (path: string) => (path === '/voices/kit' ? KIT : {}));
  api.post.mockResolvedValue({ style: 'expert', take: 1, job: 7 });
  vi.mocked(open).mockResolvedValue('C:/videos/charla.mp4');
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderImport(onDone: () => void = () => {}): void {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <ImportReference slug="spec-010" onDone={onDone} />
    </QueryClientProvider>,
  );
}

// Elige el archivo, el estilo y el tramo. La casilla de permiso la marca cada prueba cuando hace falta.
async function fillForm(start: string, end: string): Promise<void> {
  fireEvent.click(await screen.findByRole('button', { name: t('voices.import.choose') }));
  await screen.findByText('charla.mp4');
  await userEvent.click(await screen.findByRole('combobox', { name: t('voices.import.style') }));
  await userEvent.click(await screen.findByRole('option', { name: t('label.narration.style.expert') }));
  fireEvent.change(screen.getByRole('spinbutton', { name: t('voices.import.start') }), { target: { value: start } });
  fireEvent.change(screen.getByRole('spinbutton', { name: t('voices.import.end') }), { target: { value: end } });
}

function submitButton(): HTMLButtonElement {
  return screen.getByRole('button', { name: t('voices.import.submit') }) as HTMLButtonElement;
}

describe('ImportReference (spec 010, D-4)', () => {
  it('elegir archivo abre el diálogo del sistema y muestra su nombre', async () => {
    renderImport();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.import.choose') }));

    expect(await screen.findByText('charla.mp4')).toBeTruthy();
    expect(open).toHaveBeenCalledTimes(1);
  });

  it('un tramo de menos de 8 s no deja importar, y lo dice con el rango del server', async () => {
    renderImport();
    await fillForm('2', '7');

    expect(await screen.findByText(t('error.invalid_span', { low: 8, high: 12 }))).toBeTruthy();
    expect(submitButton().disabled).toBe(true);
  });

  it('sin la casilla de permiso no se puede importar', async () => {
    renderImport();
    await fillForm('2', '12');

    expect(submitButton().disabled).toBe(true);
  });

  it('importar manda el archivo, el tramo, el estilo y el permiso al server, y vuelve a la ficha', async () => {
    const onDone = vi.fn();
    renderImport(onDone);
    await fillForm('2', '12');
    fireEvent.click(screen.getByRole('checkbox', { name: t('voice.consent.import') }));

    fireEvent.click(submitButton());

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/voices/profiles/spec-010/import', {
        path: 'C:/videos/charla.mp4',
        start: 2,
        end: 12,
        style: 'expert',
        consent: true,
      }),
    );
    await waitFor(() => expect(onDone).toHaveBeenCalledTimes(1));
  });

  it('si el server rechaza el permiso, lo muestra con su texto del catálogo', async () => {
    api.post.mockRejectedValue(new ApiError(422, { code: 'consent_required', params: {}, message: '' }));
    renderImport();
    await fillForm('2', '12');
    fireEvent.click(screen.getByRole('checkbox', { name: t('voice.consent.import') }));

    fireEvent.click(submitButton());

    expect(await screen.findByText(t('error.consent_required'))).toBeTruthy();
  });
});

const SOURCE = { duration: 20, peaks: [0.2, 0.6, 0.4] };

describe('ImportReference: el tramo sobre la onda del origen (spec 010, D-4)', () => {
  beforeEach(() => {
    api.get.mockImplementation(async (path: string) => {
      if (path === '/voices/kit') return KIT;
      if (path.startsWith('/voices/import/peaks')) return SOURCE;
      return {};
    });
  });

  it('al elegir el archivo pide su onda y propone el tramo de 0 a 10 s', async () => {
    renderImport();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.import.choose') }));

    expect(await screen.findByTestId('span-picker')).toBeTruthy();
    expect(api.get).toHaveBeenCalledWith(`/voices/import/peaks?path=${encodeURIComponent('C:/videos/charla.mp4')}&n=800`);
    expect((screen.getByRole('spinbutton', { name: t('voices.import.start') }) as HTMLInputElement).value).toBe('0');
    expect((screen.getByRole('spinbutton', { name: t('voices.import.end') }) as HTMLInputElement).value).toBe('10');
  });

  it('mover la región sobre la onda cambia el inicio y el fin de los campos', async () => {
    renderImport();
    fireEvent.click(await screen.findByRole('button', { name: t('voices.import.choose') }));

    fireEvent.click(await screen.findByTestId('span-picker'));

    await waitFor(() => expect((screen.getByRole('spinbutton', { name: t('voices.import.start') }) as HTMLInputElement).value).toBe('2'));
    expect((screen.getByRole('spinbutton', { name: t('voices.import.end') }) as HTMLInputElement).value).toBe('12');
  });
});
