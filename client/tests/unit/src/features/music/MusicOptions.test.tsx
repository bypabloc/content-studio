import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { MusicOptions } from '@/features/music/MusicOptions';
import { t } from '@/shared/i18n/t';

function renderOptions(overrides: Partial<Parameters<typeof MusicOptions>[0]> = {}) {
  const handlers = {
    onVariants: vi.fn(),
    onNoLm: vi.fn(),
    onEvaluate: vi.fn(),
    onRetries: vi.fn(),
  };
  render(
    <MusicOptions
      variants={1}
      noLm={false}
      evaluate={true}
      retries={1}
      {...handlers}
      {...overrides}
    />,
  );
  return handlers;
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('MusicOptions (spec 011, D-6)', () => {
  it('WHEN se abre Avanzado THEN aparecen las variantes, sin LM, evaluar la voz y los reintentos', async () => {
    const user = userEvent.setup();
    renderOptions();

    expect(screen.queryByRole('spinbutton', { name: t('music.options.variants') })).toBeNull();
    await user.click(screen.getByRole('button', { name: t('music.advanced') }));

    expect(screen.getByRole('spinbutton', { name: t('music.options.variants') })).not.toBeNull();
    expect(screen.getByRole('button', { name: t('music.options.noLm') }).getAttribute('aria-pressed')).toBe('false');
    expect(screen.getByRole('button', { name: t('music.options.evaluate') }).getAttribute('aria-pressed')).toBe('true');
  });

  it('WHEN se escriben 2 variantes THEN avisa con 2, y un número fuera de 1–6 no avisa', async () => {
    const user = userEvent.setup();
    const { onVariants } = renderOptions();
    await user.click(screen.getByRole('button', { name: t('music.advanced') }));
    const variants = screen.getByRole('spinbutton', { name: t('music.options.variants') });

    await user.clear(variants);
    await user.type(variants, '2');
    expect(onVariants).toHaveBeenLastCalledWith(2);

    onVariants.mockClear();
    await user.clear(variants);
    await user.type(variants, '9');
    expect(onVariants).not.toHaveBeenCalled();
  });

  it('WHEN se pulsa sin LM y evaluar la voz THEN avisa con el valor contrario', async () => {
    const user = userEvent.setup();
    const { onNoLm, onEvaluate } = renderOptions();
    await user.click(screen.getByRole('button', { name: t('music.advanced') }));

    await user.click(screen.getByRole('button', { name: t('music.options.noLm') }));
    await user.click(screen.getByRole('button', { name: t('music.options.evaluate') }));

    expect(onNoLm).toHaveBeenCalledWith(true);
    expect(onEvaluate).toHaveBeenCalledWith(false);
  });

  it('WHEN se escriben reintentos válidos THEN avisa con el número', async () => {
    const user = userEvent.setup();
    const { onRetries } = renderOptions({ retries: 0 });
    await user.click(screen.getByRole('button', { name: t('music.advanced') }));
    const retries = screen.getByRole('spinbutton', { name: t('music.options.retries') });

    await user.clear(retries);
    await user.type(retries, '2');

    expect(onRetries).toHaveBeenLastCalledWith(2);
  });
});
