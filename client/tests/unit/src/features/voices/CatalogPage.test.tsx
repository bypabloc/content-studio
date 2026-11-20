import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CatalogPage } from '@/features/voices/CatalogPage';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
    fileUrl: (path: string) => `http://127.0.0.1:9000/files?path=${encodeURIComponent(path)}`,
  },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

// WaveSurfer no corre fuera del navegador: el stub deja ver qué muestra recibe el reproductor.
vi.mock('@/shared/media/Player', async () => {
  const { createElement } = await import('react');
  return { Player: ({ src }: { src: string }) => createElement('p', null, `reproductor ${src}`) };
});

const MARIA_SAMPLE = 'server/data/narration/voices/maria/neutral.wav';
const CATALOG = {
  voices: [
    {
      id: 'yesid',
      language: 'es',
      license: 'CC0',
      description: 'Voz masculina',
      favorite: false,
      state: 'not_built',
      styles: [{ style: 'neutral', approved: false, path: null }],
    },
    {
      id: 'maria',
      language: 'es',
      license: 'CC-BY',
      description: 'Voz femenina',
      favorite: false,
      state: 'approved',
      styles: [{ style: 'neutral', approved: true, path: MARIA_SAMPLE }],
    },
  ],
};

beforeEach(() => {
  api.get.mockImplementation(async (path: string) => {
    if (path === '/voices/catalog') return CATALOG;
    if (path === '/settings/voices.favorites') return { key: 'voices.favorites', value: [] };
    if (path.startsWith('/media/peaks')) return { peaks: [0.5] };
    return {};
  });
  api.put.mockImplementation(async (_path: string, body: { value: unknown }) => ({ key: 'voices.favorites', value: body.value }));
  api.post.mockResolvedValue({ id: 1, kind: 'voice.build', status: 'queued' });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderPage(): void {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <CatalogPage />
    </QueryClientProvider>,
  );
}

describe('CatalogPage (spec 010, D-5 y AC-7)', () => {
  it('muestra cada voz con su licencia y su estado', async () => {
    renderPage();

    expect(await screen.findByText('yesid')).toBeTruthy();
    expect(screen.getByText(t('voices.catalog.license', { license: 'CC0' }))).toBeTruthy();
    expect(screen.getByText(t('voices.catalog.state.not_built'))).toBeTruthy();
    expect(screen.getByText(t('voices.catalog.state.approved'))).toBeTruthy();
  });

  it('marcar una voz como favorita la guarda en las preferencias', async () => {
    renderPage();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.catalog.favorite_of', { name: 'maria' }) }));

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/settings/voices.favorites', { value: ['maria'] }));
  });

  it('Construir encola la voz como trabajo voice.build de la cola', async () => {
    renderPage();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.catalog.build_named', { name: 'yesid' }) }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', { kind: 'voice.build', params: { voices: ['yesid'], force: false } }),
    );
  });

  it('Construir todas encola todas las voces del catálogo', async () => {
    renderPage();

    fireEvent.click(await screen.findByRole('button', { name: t('voices.catalog.build_all') }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', { kind: 'voice.build', params: { voices: ['yesid', 'maria'], force: false } }),
    );
  });

  it('Forzar reconstruye aunque la voz ya esté aprobada', async () => {
    renderPage();

    fireEvent.click(await screen.findByRole('checkbox', { name: t('voices.catalog.force') }));
    fireEvent.click(screen.getByRole('button', { name: t('voices.catalog.build_named', { name: 'maria' }) }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', { kind: 'voice.build', params: { voices: ['maria'], force: true } }),
    );
  });

  it('una muestra aprobada se reproduce desde su ruta, con su forma de onda', async () => {
    renderPage();

    expect(await screen.findByText(`reproductor ${api.fileUrl(MARIA_SAMPLE)}`)).toBeTruthy();
  });

  it('una voz parcial se marca como parcial', async () => {
    api.get.mockImplementation(async (path: string) => {
      if (path === '/voices/catalog') return { voices: [{ ...CATALOG.voices[0], id: 'lucia', state: 'partial' }] };
      if (path === '/settings/voices.favorites') return { key: 'voices.favorites', value: [] };
      return {};
    });
    renderPage();

    expect(await screen.findByText(t('voices.catalog.state.partial'))).toBeTruthy();
  });

  it('una voz sin licencia ni descripción no muestra esas líneas, y una muestra sin ruta no se reproduce', async () => {
    api.get.mockImplementation(async (path: string) => {
      if (path === '/voices/catalog') {
        return {
          voices: [
            {
              id: 'lucia',
              language: null,
              license: null,
              description: null,
              favorite: false,
              state: 'approved',
              styles: [{ style: 'neutral', approved: true, path: null }],
            },
          ],
        };
      }
      if (path === '/settings/voices.favorites') return { key: 'voices.favorites', value: [] };
      return {};
    });
    renderPage();

    expect(await screen.findByText('lucia')).toBeTruthy();
    expect(screen.queryByText(/^reproductor/)).toBeNull();
  });

  it('quitar la favorita de una voz la saca de las preferencias', async () => {
    api.get.mockImplementation(async (path: string) => {
      if (path === '/voices/catalog') return CATALOG;
      if (path === '/settings/voices.favorites') return { key: 'voices.favorites', value: ['maria'] };
      if (path.startsWith('/media/peaks')) return { peaks: [0.5] };
      return {};
    });
    renderPage();

    const star = await screen.findByRole('button', { name: t('voices.catalog.favorite_of', { name: 'maria' }) });
    // La preferencia llega en otra consulta: se espera a que ★ esté marcada antes de pulsar.
    await waitFor(() => expect(star.getAttribute('aria-pressed')).toBe('true'));
    fireEvent.click(star);

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/settings/voices.favorites', { value: [] }));
  });
});
