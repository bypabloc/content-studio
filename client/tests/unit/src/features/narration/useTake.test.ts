import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useTake } from '@/features/narration/useTake';
import type { components } from '@/shared/api/schema';

type Job = components['schemas']['Job'];

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

beforeEach(() => {
  api.get.mockImplementation(async (path: string) => {
    if (path.includes('script.json')) return { wav: 'voxcpm2-expert.wav', segments: [{ text: 'Hola.' }] };
    if (path.includes('.json')) return { seed: 42, duration_s: 2.5, evaluation: null };
    if (path.startsWith('/media/info')) return { duration: 2.5, lufs: -16.2, true_peak: -1.4 };
    return { peaks: [0.1] };
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function withClient() {
  const client = new QueryClient();
  return ({ children }: { children: ReactNode }) => createElement(QueryClientProvider, { client }, children);
}

describe('useTake', () => {
  it('lee el guion y la toma de la carpeta del trabajo, y deriva el .wav y su .json', async () => {
    const job = { id: 3, output_dir: 'D:/out/narration/x' } as unknown as Job;
    const { result } = renderHook(() => useTake(job), { wrapper: withClient() });

    await waitFor(() => expect(result.current.take.data).toEqual({ seed: 42, duration_s: 2.5, evaluation: null }));
    expect(result.current.wav).toBe('D:/out/narration/x/voxcpm2-expert.wav');
    expect(api.get).toHaveBeenCalledWith('/files?path=D%3A%2Fout%2Fnarration%2Fx%2Fscript.json');
    expect(api.get).toHaveBeenCalledWith('/files?path=D%3A%2Fout%2Fnarration%2Fx%2Fvoxcpm2-expert.json');
  });

  it('sin carpeta de salida no pide nada', () => {
    const job = { id: 3, output_dir: null } as unknown as Job;
    renderHook(() => useTake(job), { wrapper: withClient() });

    expect(api.get).not.toHaveBeenCalled();
  });
});
