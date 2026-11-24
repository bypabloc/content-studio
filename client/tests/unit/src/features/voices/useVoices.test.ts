import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useKit, useProfile, useProfileMutations, useProfiles } from '@/features/voices/useVoices';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), del: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

function wrapperWith(client: QueryClient) {
  return ({ children }: { children: ReactNode }) => createElement(QueryClientProvider, { client }, children);
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('useVoices (spec 010, D-6)', () => {
  it('useProfiles pide la lista de perfiles', async () => {
    const list = [{ id: 'spec-010', name: 'Spec 010', styles: ['neutral'] }];
    api.get.mockResolvedValue(list);

    const { result } = renderHook(() => useProfiles(), { wrapper: wrapperWith(new QueryClient()) });

    await waitFor(() => expect(result.current.data).toEqual(list));
    expect(api.get).toHaveBeenCalledWith('/voices/profiles');
  });

  it('useProfile pide la ficha del perfil por su slug', async () => {
    api.get.mockResolvedValue({ id: 'spec-010', name: 'Spec 010', styles: [] });

    const { result } = renderHook(() => useProfile('spec-010'), { wrapper: wrapperWith(new QueryClient()) });

    await waitFor(() => expect(result.current.data?.name).toBe('Spec 010'));
    expect(api.get).toHaveBeenCalledWith('/voices/profiles/spec-010');
  });

  it('useKit pide los estilos del kit', async () => {
    api.get.mockResolvedValue({ styles: [{ style: 'neutral', optional: false }] });

    const { result } = renderHook(() => useKit(), { wrapper: wrapperWith(new QueryClient()) });

    await waitFor(() => expect(result.current.data?.styles).toHaveLength(1));
    expect(api.get).toHaveBeenCalledWith('/voices/kit');
  });

  it('crear, renombrar y borrar llaman a su ruta y refrescan todo lo de voces', async () => {
    api.post.mockResolvedValue({ id: 'voz', name: 'Voz' });
    api.patch.mockResolvedValue({ id: 'spec-010', name: 'Nuevo' });
    api.del.mockResolvedValue(undefined);
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, 'invalidateQueries');
    const { result } = renderHook(() => useProfileMutations(), { wrapper: wrapperWith(client) });

    await act(async () => {
      await result.current.create.mutateAsync('Voz');
    });
    await act(async () => {
      await result.current.rename.mutateAsync({ id: 'spec-010', name: 'Nuevo' });
    });
    await act(async () => {
      await result.current.remove.mutateAsync('spec-010');
    });

    expect(api.post).toHaveBeenCalledWith('/voices/profiles', { name: 'Voz' });
    expect(api.patch).toHaveBeenCalledWith('/voices/profiles/spec-010', { name: 'Nuevo' });
    expect(api.del).toHaveBeenCalledWith('/voices/profiles/spec-010?confirm=true');
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['voices'] });
  });
});
