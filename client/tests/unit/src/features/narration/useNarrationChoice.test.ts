import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { type NarrationChoice, narrationParams, useNarrationChoice } from '@/features/narration/useNarrationChoice';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const CATALOG = {
  engines: [
    { id: 'voxcpm2', license: 'Apache-2.0', commercial: true, installed: true, recommended: true, note: '', batch: false },
    { id: 'omnivoice', license: 'CC-BY-NC-4.0', commercial: false, installed: true, recommended: false, note: '', batch: true },
  ],
  styles: [
    { id: 'expert', recommended: true },
    { id: 'dramatic', recommended: false },
  ],
  voices: [
    { id: 'yesid', language: 'es' },
    { id: 'ana', language: 'es' },
  ],
};

// Lo que hay guardado en settings en cada test; lo que no está, se lee como «nunca se guardó».
let saved: Record<string, unknown> = {};

beforeEach(() => {
  saved = {};
  api.get.mockImplementation(async (path: string) => {
    if (path === '/catalog/narration') return CATALOG;
    const key = path.replace('/settings/', '');
    return { key, value: saved[key] ?? null };
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderChoice() {
  const client = new QueryClient();
  const wrapper = ({ children }: { children: ReactNode }) => createElement(QueryClientProvider, { client }, children);
  return renderHook(() => useNarrationChoice(), { wrapper });
}

const CHOICE: NarrationChoice = {
  engines: [],
  styles: [],
  voices: [],
  model: 'voxcpm2',
  style: 'expert',
  voice: 'yesid',
  language: 'es',
  master: 'voice',
  lufs: -16,
  seed: null,
  batch: null,
  evaluate: false,
  retries: 0,
};

describe('useNarrationChoice', () => {
  it('sin ajustes guardados elige lo recomendado, la primera voz y los valores por defecto', async () => {
    const { result } = renderChoice();

    await waitFor(() => expect(result.current.model).toBe('voxcpm2'));
    expect(result.current.style).toBe('expert');
    expect(result.current.voice).toBe('yesid');
    expect(result.current.language).toBe('es');
    expect(result.current).toMatchObject({ master: 'voice', lufs: -16, seed: null, batch: null, evaluate: false, retries: 0 });
  });

  it('un ajuste guardado que sigue en la lista gana a la recomendada', async () => {
    saved['select.narration.model'] = 'omnivoice';
    saved['select.narration.voice'] = 'ana';
    const { result } = renderChoice();

    await waitFor(() => expect(result.current.model).toBe('omnivoice'));
    expect(result.current.voice).toBe('ana');
  });

  it('un ajuste guardado que ya no existe vuelve a la recomendada', async () => {
    saved['select.narration.model'] = 'retirado';
    const { result } = renderChoice();

    await waitFor(() => expect(result.current.engines).toHaveLength(2));
    expect(result.current.model).toBe('voxcpm2');
  });

  it('narrationParams omite lo apagado: sin voz, semilla, lote ni evaluación', () => {
    expect(narrationParams({ ...CHOICE, voice: '' }, { text: 'Hola.' })).toEqual({
      model: 'voxcpm2',
      style: 'expert',
      language: 'es',
      master: 'voice',
      lufs: -16,
      text: 'Hola.',
    });
  });

  it('narrationParams manda la semilla, el lote, la evaluación con sus reintentos y el archivo cuando están puestos', () => {
    const params = narrationParams(
      { ...CHOICE, seed: 7, batch: 4, evaluate: true, retries: 2 },
      { file: ['C:/guiones/a.txt'] },
    );

    expect(params).toEqual({
      model: 'voxcpm2',
      style: 'expert',
      voice: 'yesid',
      language: 'es',
      master: 'voice',
      lufs: -16,
      seed: 7,
      batch: 4,
      evaluate: true,
      retries: 2,
      file: ['C:/guiones/a.txt'],
    });
  });
});
