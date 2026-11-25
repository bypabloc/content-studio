import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { JobDetail } from '@/features/library/JobDetail';
import { ApiError } from '@/shared/api/errors';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderDetail(id: number, onClose = vi.fn()) {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <JobDetail id={id} onClose={onClose} />
    </QueryClientProvider>,
  );
  return onClose;
}

describe('JobDetail (spec 031, AC-2)', () => {
  it('WHEN el trabajo existe THEN muestra su tipo, su estado y su salida', async () => {
    api.get.mockResolvedValueOnce({ id: 42, kind: 'narration', status: 'done', output_dir: 'out/narration/x' });
    renderDetail(42);
    expect(await screen.findByText('narration')).toBeTruthy();
    expect(screen.getByText('done')).toBeTruthy();
    expect(api.get).toHaveBeenCalledWith('/jobs/42');
  });

  it('AC-2: WHEN el id no existe THEN muestra el error de la API', async () => {
    const error = new ApiError(404, { code: 'job_not_found', params: { job_id: 9 }, message: 'No existe el trabajo 9' });
    api.get.mockRejectedValueOnce(error);
    renderDetail(9);
    expect(await screen.findByText(error.message)).toBeTruthy();
  });

  it('WHEN se pulsa Cerrar THEN avisa a la biblioteca', async () => {
    const user = userEvent.setup();
    api.get.mockResolvedValueOnce({ id: 1, kind: 'music', status: 'done', output_dir: null });
    const onClose = renderDetail(1);
    await user.click(screen.getByRole('button', { name: t('media.dialog.close') }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
