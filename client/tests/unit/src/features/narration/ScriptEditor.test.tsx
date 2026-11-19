import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ScriptEditor } from '@/features/narration/ScriptEditor';
import { t } from '@/shared/i18n/t';

// La API del lint: el test responde a mano, como lo haría el server.
const { post } = vi.hoisted(() => ({ post: vi.fn() }));
vi.mock('@/shared/api/context', () => ({ useApi: () => ({ post }) }));

// La importación usa las APIs de Tauri: aquí solo se evita que las llame.
vi.mock('@tauri-apps/api/webview', () => ({
  getCurrentWebview: () => ({ onDragDropEvent: () => Promise.resolve(() => {}) }),
}));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn() }));

const RULE_6 = 'Sin ";": usa punto o coma.';
const ONE_ISSUE = {
  issues: [{ rule: 6, code: 'semicolon', line: 1, col: 5, length: 1, params: { text: ';' }, message: RULE_6 }],
  words: 2,
  seconds: 1.5,
  guide: 'formato-guion.md#reglas-obligatorias',
};

function Harness() {
  const [text, setText] = useState('');
  return <ScriptEditor value={text} narrationStyle="expert" onChange={setText} onImport={() => {}} />;
}

function renderEditor() {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <Harness />
    </QueryClientProvider>,
  );
  return screen.getByRole('textbox', { name: t('narration.editor.label') });
}

afterEach(() => {
  cleanup();
  post.mockReset();
  Reflect.deleteProperty(window, '__TAURI_INTERNALS__');
});

describe('ScriptEditor', () => {
  it('AC-6: a los 300 ms del último cambio pide el lint y subraya el ; con el texto de la regla 6', async () => {
    post.mockResolvedValue(ONE_ISSUE);
    const textarea = renderEditor();

    fireEvent.change(textarea, { target: { value: 'Hola; mundo' } });

    expect(post).not.toHaveBeenCalled();
    const mark = await screen.findByTitle(RULE_6);
    expect(mark.textContent).toBe(';');
    expect(post).toHaveBeenCalledWith('/narration/lint', { text: 'Hola; mundo', style: 'expert' });
  });

  it('muestra las palabras, los segundos estimados y el número de avisos', async () => {
    post.mockResolvedValue(ONE_ISSUE);
    const textarea = renderEditor();

    fireEvent.change(textarea, { target: { value: 'Hola; mundo' } });

    expect(await screen.findByText('2 palabras · 2 s')).toBeTruthy();
    expect(screen.getByText('1 aviso')).toBeTruthy();
  });

  it('«Importar» abre el diálogo y manda al editor los guiones que se eligen', async () => {
    Object.assign(window, { __TAURI_INTERNALS__: {} }); // el botón solo abre el diálogo dentro de la ventana
    vi.mocked(open).mockResolvedValue(['C:/g/a.txt']);
    const onImport = vi.fn();
    render(
      <QueryClientProvider client={new QueryClient()}>
        <ScriptEditor value="" narrationStyle="expert" onChange={() => {}} onImport={onImport} />
      </QueryClientProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: t('narration.import.button') }));

    await waitFor(() => expect(onImport).toHaveBeenCalledWith(['C:/g/a.txt']));
  });
});
