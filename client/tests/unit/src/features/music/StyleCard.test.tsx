import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import type { components } from '@/shared/api/schema';
import { StyleCard } from '@/features/music/StyleCard';
import { label, t } from '@/shared/i18n/t';

type StyleOut = components['schemas']['StyleOut'];

const withSample: StyleOut = {
  key: 'lofi-chill',
  category: 'lofi',
  musical_key: 'C Major',
  bpm: 80,
  time_signature: '4',
  caption: 'lo-fi hip hop',
  has_sample: true,
};
const withoutSample: StyleOut = { ...withSample, key: 'techno-dark', has_sample: false };

function renderCard(style: StyleOut, overrides: Partial<Parameters<typeof StyleCard>[0]> = {}) {
  const handlers = {
    onToggleFavorite: vi.fn(),
    onToggleSelect: vi.fn(),
    onPlay: vi.fn(),
  };
  render(
    <StyleCard style={style} favorite={false} selected={false} {...handlers} {...overrides} />,
  );
  return handlers;
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('StyleCard (spec 011, D-5)', () => {
  it('WHEN el estilo tiene muestra THEN ▶ la suena', async () => {
    const user = userEvent.setup();
    const { onPlay } = renderCard(withSample);

    await user.click(screen.getByRole('button', { name: t('music.style.play', { style: label('music.style', 'lofi-chill') }) }));

    expect(onPlay).toHaveBeenCalledTimes(1);
  });

  it('WHEN el estilo no tiene muestra THEN no hay ▶', () => {
    renderCard(withoutSample);

    expect(screen.queryByRole('button', { name: t('music.style.play', { style: label('music.style', 'techno-dark') }) })).toBeNull();
  });

  it('WHEN se pulsa ★ THEN cambia el favorito', async () => {
    const user = userEvent.setup();
    const { onToggleFavorite } = renderCard(withSample);

    await user.click(screen.getByRole('button', { name: t('music.style.favorite') }));

    expect(onToggleFavorite).toHaveBeenCalledTimes(1);
  });

  it('WHEN se pulsa el nombre THEN se elige o se quita del pedido', async () => {
    const user = userEvent.setup();
    const { onToggleSelect } = renderCard(withSample, { selected: true });

    await user.click(screen.getByRole('button', { name: label('music.style', 'lofi-chill') }));

    expect(onToggleSelect).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button', { name: label('music.style', 'lofi-chill') }).getAttribute('aria-pressed')).toBe(
      'true',
    );
  });
});
