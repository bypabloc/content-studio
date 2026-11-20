import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ProfileCard } from '@/features/voices/ProfileCard';
import { t } from '@/shared/i18n/t';

const PROFILE = { id: 'spec-010', name: 'Spec 010', styles: [] };

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderCard(done: number, total: number) {
  const handlers = { onOpen: vi.fn(), onRename: vi.fn(), onRemove: vi.fn() };
  render(<ProfileCard profile={PROFILE} done={done} total={total} {...handlers} />);
  return handlers;
}

describe('ProfileCard (spec 010, D-6)', () => {
  it('muestra el nombre del perfil y su progreso sobre el total', () => {
    renderCard(3, 12);

    expect(screen.getByRole('region', { name: 'Spec 010' })).toBeTruthy();
    const bar = screen.getByRole('progressbar', { name: t('voices.progress', { done: 3, total: 12 }) });
    expect(bar.getAttribute('aria-valuenow')).toBe('0.25');
  });

  it('sin total (el kit todavía no llega) no muestra progreso', () => {
    renderCard(0, 0);

    expect(screen.queryByRole('progressbar')).toBeNull();
  });

  it('cada acción llama a su manejador', () => {
    const handlers = renderCard(0, 12);

    fireEvent.click(screen.getByRole('button', { name: t('voices.open') }));
    fireEvent.click(screen.getByRole('button', { name: t('voices.rename') }));
    fireEvent.click(screen.getByRole('button', { name: t('voices.delete') }));

    expect(handlers.onOpen).toHaveBeenCalledTimes(1);
    expect(handlers.onRename).toHaveBeenCalledTimes(1);
    expect(handlers.onRemove).toHaveBeenCalledTimes(1);
  });
});
