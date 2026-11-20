import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MyVoicesPage } from '@/features/voices/MyVoicesPage';
import { ApiError } from '@/shared/api/errors';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    del: vi.fn(),
    fileUrl: (path: string) => `http://127.0.0.1:9000/files?path=${encodeURIComponent(path)}`,
  },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

// El asistente tiene sus propios tests: aquí solo importa que se abre con el perfil y que terminar vuelve al detalle.
vi.mock('@/features/recording/RecordWizard', async () => {
  const { createElement } = await import('react');
  return {
    RecordWizard: ({ slug, onDone }: { slug: string; onDone: () => void }) =>
      createElement(
        'div',
        null,
        createElement('p', null, `asistente ${slug}`),
        createElement('button', { onClick: onDone }, 'terminar'),
      ),
  };
});

// El formulario de importar tiene sus propios tests: aquí solo importa que se abre con el perfil y que terminar vuelve al detalle.
vi.mock('@/features/recording/ImportReference', async () => {
  const { createElement } = await import('react');
  return {
    ImportReference: ({ slug, onDone }: { slug: string; onDone: () => void }) =>
      createElement(
        'div',
        null,
        createElement('p', null, `importar ${slug}`),
        createElement('button', { onClick: onDone }, 'terminar importar'),
      ),
  };
});

// Los 12 estilos obligatorios del kit (spec 010, D-6) y uno opcional que no entra en el progreso.
const REQUIRED = ['neutral', 'friendly', 'expert', 'clear', 'steady', 'soft', 'energetic', 'dramatic', 'sad', 'intimate', 'neutral-en', 'neutral-end'];
const KIT = { styles: [...REQUIRED.map((style) => ({ style, optional: false })), { style: 'whisper', optional: true }] };
// Nueve de los doce obligatorios tienen referencia: el perfil va por 9 de 12.
const PROFILE = { id: 'spec-010', name: 'Spec 010', styles: REQUIRED.slice(0, 9) };

beforeEach(() => {
  api.get.mockImplementation(async (path: string) => {
    if (path === '/voices/kit') return KIT;
    if (path === '/voices/profiles') return [PROFILE];
    return { id: PROFILE.id, name: PROFILE.name, styles: [] };
  });
  api.post.mockResolvedValue({ id: 'voz-nueva', name: 'Voz nueva' });
  api.patch.mockResolvedValue({ id: 'spec-010', name: 'Voz renombrada' });
  api.del.mockResolvedValue(undefined);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderPage(): void {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MyVoicesPage />
    </QueryClientProvider>,
  );
}

describe('MyVoicesPage (spec 010, D-6)', () => {
  it('lista cada perfil con su progreso sobre los 12 estilos obligatorios', async () => {
    renderPage();

    expect(await screen.findByText('Spec 010')).toBeTruthy();
    // El progreso espera al kit (los 12 obligatorios): hasta entonces no hay total que mostrar.
    const progress = await screen.findByRole('progressbar', { name: t('voices.progress', { done: 9, total: 12 }) });
    expect(progress.getAttribute('aria-valuenow')).toBe('0.75');
  });

  it('sin perfiles dice cómo empezar', async () => {
    api.get.mockImplementation(async (path: string) => (path === '/voices/kit' ? KIT : []));
    renderPage();

    expect(await screen.findByText(t('voices.empty'))).toBeTruthy();
  });

  it('crear: pide el nombre y lo manda a la API', async () => {
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: t('voices.new') }));

    const dialog = await screen.findByRole('alertdialog');
    fireEvent.change(within(dialog).getByRole('textbox', { name: t('voices.name') }), { target: { value: 'Voz nueva' } });
    fireEvent.click(within(dialog).getByRole('button', { name: t('action.create') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/voices/profiles', { name: 'Voz nueva' }));
  });

  it('renombrar: el diálogo trae el nombre actual y manda PATCH con el nuevo', async () => {
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: t('voices.rename') }));

    const dialog = await screen.findByRole('alertdialog');
    const field = within(dialog).getByRole('textbox', { name: t('voices.name') }) as HTMLInputElement;
    expect(field.value).toBe('Spec 010');
    fireEvent.change(field, { target: { value: 'Voz renombrada' } });
    fireEvent.click(within(dialog).getByRole('button', { name: t('action.save') }));

    await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/voices/profiles/spec-010', { name: 'Voz renombrada' }));
  });

  it('borrar pide confirmación y manda el perfil a la papelera (confirm=true)', async () => {
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: t('voices.delete') }));

    const dialog = await screen.findByRole('alertdialog');
    expect(api.del).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole('button', { name: t('voices.delete.confirm') }));

    await waitFor(() => expect(api.del).toHaveBeenCalledWith('/voices/profiles/spec-010?confirm=true'));
  });

  it('un nombre repetido muestra el error de la API y no cierra el diálogo', async () => {
    const error = new ApiError(409, { code: 'profile_exists', params: { profile: 'spec-010' } });
    api.post.mockRejectedValue(error);
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: t('voices.new') }));

    const dialog = await screen.findByRole('alertdialog');
    fireEvent.change(within(dialog).getByRole('textbox', { name: t('voices.name') }), { target: { value: 'Spec 010' } });
    fireEvent.click(within(dialog).getByRole('button', { name: t('action.create') }));

    expect(await within(dialog).findByText(error.message)).toBeTruthy();
  });

  it('abrir un perfil muestra su detalle y volver regresa a la lista', async () => {
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: t('voices.open') }));
    fireEvent.click(await screen.findByRole('button', { name: t('voices.back') }));

    expect(await screen.findByRole('button', { name: t('voices.open') })).toBeTruthy();
  });

  it('Grabar abre el asistente del perfil, y terminar vuelve al detalle', async () => {
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: t('voices.open') }));
    fireEvent.click(await screen.findByRole('button', { name: t('voices.record.open') }));
    expect(await screen.findByText('asistente spec-010')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'terminar' }));

    expect(await screen.findByRole('button', { name: t('voices.back') })).toBeTruthy();
  });

  it('Importar abre el formulario del perfil, y terminar vuelve al detalle', async () => {
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: t('voices.open') }));
    fireEvent.click(await screen.findByRole('button', { name: t('voices.import.open') }));
    expect(await screen.findByText('importar spec-010')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'terminar importar' }));

    expect(await screen.findByRole('button', { name: t('voices.back') })).toBeTruthy();
  });
});
