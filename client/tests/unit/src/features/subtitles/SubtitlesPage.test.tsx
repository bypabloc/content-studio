import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { SubtitlesPage } from '@/features/subtitles/SubtitlesPage';
import { t } from '@/shared/i18n/t';

const { api, open } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn(), fileUrl: (path: string) => `file://${path}` },
  open: vi.fn(),
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }));
// El editor se prueba aparte (SubtitlesEditor, SubtitlesPreview): aquí solo se comprueba que se abre y se cierra.
vi.mock('@/features/subtitles/SubtitlesPreview', () => ({ SubtitlesPreview: () => null }));

function renderPage() {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <SubtitlesPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  api.get.mockResolvedValue([]);
  api.post.mockResolvedValue({ id: 1 });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('SubtitlesPage', () => {
  it('muestra el estado vacío cuando no hay proyectos', async () => {
    renderPage();

    expect(await screen.findByText(t('subtitles.home.empty'))).toBeTruthy();
  });

  it('encola la creación con el origen elegido y la ruta escrita', async () => {
    renderPage();
    fireEvent.change(await screen.findByLabelText(t('subtitles.home.input')), { target: { value: 'charla.wav' } });

    fireEvent.click(screen.getByRole('button', { name: t('subtitles.home.create') }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', {
        kind: 'subtitles.create',
        params: { origin: 'file', input: 'charla.wav' },
      }),
    );
  });

  it('picks the input with the system dialog and sends the chosen origin', async () => {
    open.mockResolvedValue('D:/media/charla.wav');
    renderPage();

    await userEvent.click(await screen.findByRole('combobox', { name: t('subtitles.home.origin') }));
    await userEvent.click(await screen.findByRole('option', { name: t('subtitles.origin.cleaner') }));
    fireEvent.click(screen.getByRole('button', { name: t('subtitles.home.pick') }));
    await waitFor(() =>
      expect(screen.getByLabelText(t('subtitles.home.input'))).toHaveProperty('value', 'D:/media/charla.wav'),
    );

    fireEvent.click(screen.getByRole('button', { name: t('subtitles.home.create') }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', {
        kind: 'subtitles.create',
        params: { origin: 'cleaner', input: 'D:/media/charla.wav' },
      }),
    );
  });

  it('opens a saved project in its editor and goes back to the list', async () => {
    const project = { id: 3, name: 'charla', source_path: 'charla.mp4', updated_at: '2026-11-22' };
    const doc = { version: 1, source: { path: 'charla.mp4', kind: 'file' }, language: 'es', style: {}, tracks: {}, cues: [] };
    api.get.mockImplementation(async (path: string) => (path === '/subtitles' ? [project] : doc));
    renderPage();

    fireEvent.click(await screen.findByRole('button', { name: t('subtitles.home.open') }));
    fireEvent.click(await screen.findByRole('button', { name: t('subtitles.home.back') }));

    expect(await screen.findByText('charla')).toBeTruthy();
  });
});
