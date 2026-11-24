import { act, renderHook, waitFor } from '@testing-library/react';
import { listen } from '@tauri-apps/api/event';
import { describe, expect, it, vi } from 'vitest';

import { useBootstrapProgress } from '@/bootstrap/useBootstrapProgress';

vi.mock('@tauri-apps/api/event', () => ({ listen: vi.fn() }));

describe('useBootstrapProgress (spec 022, D-2)', () => {
  it('junta los eventos bootstrap de Tauri por paso y deja de escuchar al desmontar', async () => {
    let handler: ((event: { payload: unknown }) => void) | undefined;
    const stopListening = vi.fn();
    vi.mocked(listen).mockImplementation(async (_name, callback) => {
      handler = callback as typeof handler;
      return stopListening;
    });

    const { result, unmount } = renderHook(() => useBootstrapProgress());
    await act(async () => {});
    act(() => handler?.({ payload: { step: 'python', state: 'running', log: 'L' } }));
    act(() => handler?.({ payload: { step: 'python', state: 'done', log: 'L' } }));

    expect(listen).toHaveBeenCalledWith('bootstrap', expect.any(Function));
    expect(result.current).toEqual({ steps: { python: 'done' }, log: 'L' });
    unmount();
    await waitFor(() => expect(stopListening).toHaveBeenCalled());
  });
});
