import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NarrationPage } from '@/features/narration/NarrationPage';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

// El importador: el test guarda el callback que la pantalla le pasa, y lo llama con rutas a mano (AC-9).
const { importer } = vi.hoisted(() => ({ importer: { onImport: (_paths: string[]) => {} } }));
vi.mock('@/features/narration/useScriptImport', () => ({
  useScriptImport: (onImport: (paths: string[]) => void) => {
    importer.onImport = onImport;
    return { pick: () => Promise.resolve() };
  },
}));

// El resultado tiene su propio test: aquí solo importa qué toma le llega.
vi.mock('@/features/narration/NarrationResult', async () => {
  const { createElement } = await import('react');
  return { NarrationResult: ({ job }: { job: { id: number } }) => createElement('p', null, `resultado ${job.id}`) };
});

const CATALOG = {
  engines: [
    { id: 'voxcpm2', license: 'Apache-2.0', commercial: true, installed: true, recommended: true, note: '', batch: false },
  ],
  styles: [{ id: 'expert', recommended: true }],
  voices: [{ id: 'yesid', language: 'es' }],
};
const CLEAN_LINT = { issues: [], words: 3, seconds: 2, guide: 'formato-guion.md' };

beforeEach(() => {
  api.get.mockImplementation(async (path: string) => {
    if (path === '/jobs') return [];
    return path === '/catalog/narration' ? CATALOG : { key: path.replace('/settings/', ''), value: null };
  });
  api.put.mockImplementation(async (path: string, body: { value: unknown }) => ({ key: path, value: body.value }));
  api.post.mockImplementation(async (path: string) => (path === '/jobs' ? { id: 1 } : CLEAN_LINT));
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Espera a que llegue el catálogo: sin motor ni estilo, Generar e importar no encolan nada.
async function renderPage(): Promise<HTMLTextAreaElement> {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <NarrationPage />
    </QueryClientProvider>,
  );
  // Con un solo motor, el selector lo muestra como valor fijo (AC-5): se espera su texto.
  await screen.findAllByText('★ voxcpm2');
  return screen.getByRole('textbox', { name: t('narration.editor.label') }) as HTMLTextAreaElement;
}

function jobsPosted(): unknown[] {
  return api.post.mock.calls.filter(([path]) => path === '/jobs').map(([, body]) => body);
}

describe('NarrationPage', () => {
  it('AC-8: Ctrl+Enter encola la narración con el texto y las opciones elegidas', async () => {
    const textarea = await renderPage();
    fireEvent.change(textarea, { target: { value: 'Hola, mundo.' } });

    fireEvent.keyDown(window, { key: 'Enter', ctrlKey: true });

    await waitFor(() =>
      expect(jobsPosted()).toEqual([
        {
          kind: 'narration',
          params: expect.objectContaining({
            text: 'Hola, mundo.',
            model: 'voxcpm2',
            style: 'expert',
            voice: 'yesid',
            language: 'es',
            master: 'voice',
            lufs: -16,
          }),
        },
      ]),
    );
  });

  it('Generar lleva su ícono de narración y su texto (spec 009, D-5)', async () => {
    await renderPage();

    const generate = screen.getByRole('button', { name: t('narration.generate') });
    expect(generate.textContent).toBe(t('narration.generate'));
    expect(generate.querySelector('svg.lucide-audio-lines')).not.toBeNull();
  });

  it('mientras llega el catálogo, Generar no encola un trabajo sin motor ni estilo', async () => {
    api.get.mockImplementation(async (path: string) => (path === '/catalog/narration' ? new Promise(() => {}) : null));
    render(
      <QueryClientProvider client={new QueryClient()}>
        <NarrationPage />
      </QueryClientProvider>,
    );
    const textarea = (await screen.findByRole('textbox', { name: t('narration.editor.label') })) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'Hola, mundo.' } });

    fireEvent.keyDown(window, { key: 'Enter', ctrlKey: true });

    expect(jobsPosted()).toEqual([]);
  });

  it('sin texto, Ctrl+Enter no encola nada', async () => {
    await renderPage();

    fireEvent.keyDown(window, { key: 'Enter', ctrlKey: true });

    expect(jobsPosted()).toEqual([]);
  });

  it('AC-9: cada guion importado se encola como un trabajo propio', async () => {
    await renderPage();

    importer.onImport(['C:/g/a.txt', 'C:/g/b.json']);

    await waitFor(() =>
      expect(jobsPosted()).toEqual([
        { kind: 'narration', params: expect.objectContaining({ file: ['C:/g/a.txt'] }) },
        { kind: 'narration', params: expect.objectContaining({ file: ['C:/g/b.json'] }) },
      ]),
    );
  });

  it('muestra la última toma terminada de narración: no las que esperan en la cola ni las de música', async () => {
    api.get.mockImplementation(async (path: string) => {
      if (path === '/jobs') {
        return [
          { id: 3, kind: 'narration', status: 'done' },
          { id: 5, kind: 'narration', status: 'queued' },
          { id: 4, kind: 'music', status: 'done' },
          { id: 6, kind: 'narration.regenerate', status: 'done' },
        ];
      }
      return path === '/catalog/narration' ? CATALOG : { key: path.replace('/settings/', ''), value: null };
    });
    await renderPage();

    expect(await screen.findByText('resultado 6')).toBeTruthy();
  });

  it('con un solo aviso, el texto va en singular', async () => {
    api.post.mockImplementation(async (path: string) =>
      path === '/jobs' ? { id: 1 } : { ...CLEAN_LINT, issues: [{}] },
    );
    const textarea = await renderPage();
    fireEvent.change(textarea, { target: { value: 'Hola; mundo.' } });

    expect(await screen.findByText(t('narration.generate.warnings_one'))).toBeTruthy();
  });

  it('con avisos del linter, el botón lo dice y aun así deja generar', async () => {
    api.post.mockImplementation(async (path: string) =>
      path === '/jobs' ? { id: 1 } : { ...CLEAN_LINT, issues: [{}, {}] },
    );
    const textarea = await renderPage();
    fireEvent.change(textarea, { target: { value: 'Hola; mundo.' } });

    expect(await screen.findByText(t('narration.generate.warnings_other', { count: 2 }))).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: t('narration.generate') }));
    await waitFor(() => expect(jobsPosted()).toHaveLength(1));
  });
});
