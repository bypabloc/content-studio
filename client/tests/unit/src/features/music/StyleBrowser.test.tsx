import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { StyleBrowser } from '@/features/music/StyleBrowser';
import type { components } from '@/shared/api/schema';
import { label, t } from '@/shared/i18n/t';

type StyleOut = components['schemas']['StyleOut'];

const styles: StyleOut[] = [
  { key: 'lofi-chill', category: 'lofi', musical_key: 'C Major', bpm: 80, time_signature: '4', caption: 'lo-fi hip hop', has_sample: true },
  { key: 'techno-dark', category: 'electronic', musical_key: 'A Minor', bpm: 130, time_signature: '4', caption: 'dark techno', has_sample: false },
  { key: 'jazz-soft', category: 'jazz', musical_key: 'D Minor', bpm: 90, time_signature: '4', caption: 'soft jazz piano', has_sample: false },
];

type Props = Parameters<typeof StyleBrowser>[0];

function renderBrowser(overrides: Partial<Props> = {}) {
  const handlers = {
    onToggleFavorite: vi.fn(),
    onToggleSelect: vi.fn(),
    onPlay: vi.fn(),
  };
  render(<StyleBrowser styles={styles} favorites={[]} selected={[]} {...handlers} {...overrides} />);
  return handlers;
}

/** Las claves de las tarjetas visibles, en el orden en que aparecen. */
function visibleKeys(): string[] {
  return Array.from(document.querySelectorAll('[data-style]')).map((card) => card.getAttribute('data-style') ?? '');
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('StyleBrowser (spec 011, D-5)', () => {
  it('WHEN hay favoritos THEN aparecen primero', () => {
    renderBrowser({ favorites: ['techno-dark'] });

    expect(visibleKeys()).toEqual(['techno-dark', 'lofi-chill', 'jazz-soft']);
  });

  it('WHEN se escribe en el buscador THEN solo quedan los estilos que coinciden', async () => {
    const user = userEvent.setup();
    renderBrowser();

    await user.type(screen.getByRole('textbox', { name: t('music.style.search') }), 'jazz');

    expect(visibleKeys()).toEqual(['jazz-soft']);
  });

  it('WHEN se elige una categoría THEN solo quedan sus estilos', async () => {
    const user = userEvent.setup();
    renderBrowser();

    await user.click(screen.getByRole('button', { name: label('music.category', 'electronic') }));

    expect(visibleKeys()).toEqual(['techno-dark']);
  });

  it('WHEN se elige el modo menor THEN quedan los estilos en menor', async () => {
    const user = userEvent.setup();
    renderBrowser();

    await user.click(screen.getByRole('button', { name: t('music.style.mode.minor') }));

    expect(visibleKeys()).toEqual(['techno-dark', 'jazz-soft']);
  });

  it('WHEN se cambia el rango de BPM y el modo THEN el filtro sigue esos valores', async () => {
    const user = userEvent.setup();
    renderBrowser();

    await user.clear(screen.getByRole('spinbutton', { name: t('music.style.bpmMax') }));
    await user.type(screen.getByRole('spinbutton', { name: t('music.style.bpmMax') }), '100');
    expect(visibleKeys()).toEqual(['lofi-chill', 'jazz-soft']);

    await user.click(screen.getByRole('button', { name: t('music.style.mode.major') }));
    expect(visibleKeys()).toEqual(['lofi-chill']);

    await user.click(screen.getByRole('button', { name: t('music.style.mode.all') }));
    expect(visibleKeys()).toEqual(['lofi-chill', 'jazz-soft']);
  });

  it('WHEN se pulsa otra vez la categoría elegida THEN se quita el filtro', async () => {
    const user = userEvent.setup();
    renderBrowser();

    await user.click(screen.getByRole('button', { name: label('music.category', 'jazz') }));
    expect(visibleKeys()).toEqual(['jazz-soft']);

    await user.click(screen.getByRole('button', { name: label('music.category', 'jazz') }));
    expect(visibleKeys()).toEqual(['lofi-chill', 'techno-dark', 'jazz-soft']);
  });

  it('WHEN se eligen varios estilos THEN cada uno se pide por separado', async () => {
    const user = userEvent.setup();
    const { onToggleSelect } = renderBrowser();

    await user.click(screen.getByRole('button', { name: label('music.style', 'lofi-chill') }));
    await user.click(screen.getByRole('button', { name: label('music.style', 'jazz-soft') }));

    expect(onToggleSelect.mock.calls).toEqual([['lofi-chill'], ['jazz-soft']]);
  });

  it('WHEN ningún estilo coincide THEN lo dice', async () => {
    const user = userEvent.setup();
    renderBrowser();

    await user.type(screen.getByRole('textbox', { name: t('music.style.search') }), 'zzzz');

    expect(screen.queryByText(t('music.style.empty'))).not.toBeNull();
  });
});
