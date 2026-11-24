import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { AudioThumb } from '@/features/library/AudioThumb';

const { api, open, openPath } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    del: vi.fn(),
    patch: vi.fn(),
    fileUrl: (path: string) => `file://${path}`,
    queryUrl: (path: string) => `http://api${path}`,
  },
  open: vi.fn(),
  openPath: vi.fn(),
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }));
vi.mock('@tauri-apps/plugin-opener', () => ({ openPath }));

const wrap = (ui: React.ReactNode) =>
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{ui}</QueryClientProvider>);

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  window.location.hash = '';
});

describe('AudioThumb (spec 020, D-1)', () => {
  it('dibuja una barra por pico en el canvas', async () => {
    const fillRect = vi.fn();
    const context = { clearRect: vi.fn(), fillRect, fillStyle: '' };
    const getContext = vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(context as unknown as CanvasRenderingContext2D);
    api.get.mockResolvedValue({ peaks: [0, 0.5, 1] });

    wrap(<AudioThumb path="a.wav" label="onda" />);

    expect(screen.getByRole('img', { name: 'onda' })).toBeTruthy();
    await waitFor(() => expect(fillRect).toHaveBeenCalledTimes(3));
    getContext.mockRestore();
  });
});
