import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { openPath } from '@tauri-apps/plugin-opener';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { BootstrapPage } from '@/bootstrap/BootstrapPage';
import { t } from '@/shared/i18n/t';

vi.mock('@tauri-apps/plugin-opener', () => ({ openPath: vi.fn() }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('BootstrapPage (spec 022, AC-5)', () => {
  it('muestra cada paso de la preparación con su estado', () => {
    render(<BootstrapPage steps={{ python: 'done', sync: 'running' }} log={null} failed={null} onRetry={() => {}} />);

    expect(screen.getByRole('heading', { name: t('bootstrap.title') })).toBeTruthy();
    expect(screen.getByText(`${t('bootstrap.step.python')}: ${t('bootstrap.state.done')}`)).toBeTruthy();
    expect(screen.getByText(`${t('bootstrap.step.sync')}: ${t('bootstrap.state.running')}`)).toBeTruthy();
    expect(screen.getByText(`${t('bootstrap.step.seed')}: ${t('bootstrap.state.pending')}`)).toBeTruthy();
    expect(screen.queryByRole('button', { name: t('server.retry') })).toBeNull();
  });

  it('si un paso falla muestra el motivo, Reintentar y Ver log', () => {
    const onRetry = vi.fn();
    render(
      <BootstrapPage
        steps={{ python: 'done', sync: 'failed' }}
        log="C:/Users/x/AppData/Local/Content Studio/logs/bootstrap.log"
        failed="bootstrap_sync_failed"
        onRetry={onRetry}
      />,
    );

    expect(screen.getByText(t('bootstrap.error.sync'))).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: t('server.retry') }));
    expect(onRetry).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button', { name: t('bootstrap.log') }));
    expect(openPath).toHaveBeenCalledWith('C:/Users/x/AppData/Local/Content Studio/logs/bootstrap.log');
  });

  it.each([
    ['bootstrap_python_failed', 'bootstrap.error.python'],
    ['bootstrap_seed_failed', 'bootstrap.error.seed'],
  ] as const)('explica el código %s', (code, key) => {
    render(<BootstrapPage steps={{}} log={null} failed={code} onRetry={() => {}} />);

    expect(screen.getByText(t(key))).toBeTruthy();
    expect(screen.queryByRole('button', { name: t('bootstrap.log') })).toBeNull();
  });
});
