import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { UIJobPicker } from '@/shared/components/molecules/UIJobPicker';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn(), fileUrl: (path: string) => `file://${path}` },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const JOBS = [
  { id: 1, kind: 'narration', status: 'done', starred: false, params: {}, output_dir: 'out/a' },
  { id: 2, kind: 'narration', status: 'done', starred: true, params: {}, output_dir: 'out/b' },
  { id: 3, kind: 'music', status: 'done', starred: false, params: {}, output_dir: 'out/c' },
  { id: 4, kind: 'narration', status: 'running', starred: false, params: {}, output_dir: 'out/d' },
];

function renderPicker(onPick = vi.fn()) {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <UIJobPicker kinds={['narration']} label={t('mix.source.history')} onPick={onPick} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  api.get.mockResolvedValue(JOBS);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('UIJobPicker', () => {
  it('ofrece solo los trabajos terminados de esos tipos, con la ★ primero', async () => {
    renderPicker();

    await userEvent.click(await screen.findByRole('combobox', { name: t('mix.source.history') }));
    const jobs = (await screen.findAllByRole('option')).filter((option) => option.textContent?.includes('narration'));

    expect(jobs).toHaveLength(2);
    expect(jobs[0].textContent).toContain('★');
  });

  it('avisa del trabajo elegido', async () => {
    const onPick = vi.fn();
    renderPicker(onPick);

    await userEvent.click(await screen.findByRole('combobox', { name: t('mix.source.history') }));
    await userEvent.click(await screen.findByRole('option', { name: /narration #1/ }));

    expect(onPick).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }));
  });
});
