import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { useDebounced, useScriptLint } from '@/features/narration/useScriptLint';

const { post } = vi.hoisted(() => ({ post: vi.fn() }));
vi.mock('@/shared/api/context', () => ({ useApi: () => ({ post }) }));

function wrapper({ children }: { children: ReactNode }) {
  return createElement(QueryClientProvider, { client: new QueryClient() }, children);
}

describe('useDebounced', () => {
  it('cambia el valor solo cuando pasa el tiempo sin nuevos cambios', async () => {
    const { result, rerender } = renderHook(({ value }) => useDebounced(value, 50), { initialProps: { value: 'a' } });

    rerender({ value: 'ab' });

    expect(result.current).toBe('a');
    await waitFor(() => expect(result.current).toBe('ab'));
  });
});

describe('useScriptLint', () => {
  it('con el texto vacío no pide el lint', () => {
    renderHook(() => useScriptLint('   ', 'expert'), { wrapper });

    expect(post).not.toHaveBeenCalled();
  });

  it('pide el lint con el texto y el estilo, y devuelve sus avisos y palabras', async () => {
    post.mockResolvedValue({ issues: [], words: 1, seconds: 1, guide: 'formato-guion.md' });

    const { result } = renderHook(() => useScriptLint('Hola.', 'expert'), { wrapper });

    await waitFor(() => expect(result.current.data?.words).toBe(1));
    expect(post).toHaveBeenCalledWith('/narration/lint', { text: 'Hola.', style: 'expert' });
  });
});
