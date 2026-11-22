import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { BUILTIN_PRESETS, recommendedPreset } from '@/features/subtitles/presets';
import { StylePanel } from '@/features/subtitles/StylePanel';
import { t } from '@/shared/i18n/t';

// Las preferencias viven en settings: aquí son un mapa en memoria, con el mismo contrato que useSetting.
const { settings } = vi.hoisted(() => ({ settings: new Map<string, unknown>() }));
vi.mock('@/shared/hooks/useSetting', () => ({
  useSetting: <T,>(key: string, fallback: T): [T, (value: T) => void] => [
    (settings.has(key) ? settings.get(key) : fallback) as T,
    (value: T) => settings.set(key, value),
  ],
}));

describe('StylePanel', () => {
  beforeEach(() => settings.clear());
  afterEach(cleanup);

  it('recommends reels for a vertical video and classic for a wide one', () => {
    expect(recommendedPreset(9 / 16)).toBe('reels');
    expect(recommendedPreset(16 / 9)).toBe('classic');
  });

  it('saves the style as a named preset, which stays the last used one after reopening', async () => {
    const onStyleChange = vi.fn();
    const { unmount } = render(<StylePanel style={BUILTIN_PRESETS.classic} aspect={16 / 9} onStyleChange={onStyleChange} />);

    fireEvent.change(screen.getByRole('textbox', { name: t('subtitles.style.presetName') }), {
      target: { value: 'Mi estilo' },
    });
    fireEvent.click(screen.getByRole('button', { name: t('subtitles.style.saveAs') }));

    expect(settings.get('subtitles.presets')).toEqual([{ name: 'Mi estilo', style: BUILTIN_PRESETS.classic }]);
    expect(settings.get('select.subtitles.preset')).toBe('own:Mi estilo');
    unmount();

    render(<StylePanel style={BUILTIN_PRESETS.classic} aspect={16 / 9} onStyleChange={onStyleChange} />);
    const select = (await screen.findByRole('combobox', { name: t('subtitles.style.preset') })) as HTMLInputElement;
    expect(select.value).toBe('Mi estilo');
  });

  it('applies the built-in preset that is chosen', async () => {
    const onStyleChange = vi.fn();
    render(<StylePanel style={BUILTIN_PRESETS.classic} aspect={16 / 9} onStyleChange={onStyleChange} />);

    await userEvent.click(await screen.findByRole('combobox', { name: t('subtitles.style.preset') }));
    await userEvent.click(await screen.findByRole('option', { name: (name) => name.includes(t('subtitles.preset.reels')) }));

    expect(onStyleChange).toHaveBeenCalledWith(BUILTIN_PRESETS.reels);
  });

  it('applies an own preset from the list', async () => {
    settings.set('subtitles.presets', [{ name: 'Mío', style: BUILTIN_PRESETS.minimal }]);
    const onStyleChange = vi.fn();
    render(<StylePanel style={BUILTIN_PRESETS.classic} aspect={16 / 9} onStyleChange={onStyleChange} />);

    await userEvent.click(await screen.findByRole('combobox', { name: t('subtitles.style.preset') }));
    await userEvent.click(await screen.findByRole('option', { name: 'Mío' }));

    expect(onStyleChange).toHaveBeenCalledWith(BUILTIN_PRESETS.minimal);
  });

  it('passes the uppercase and pop switches up with the rest of the style', () => {
    const onStyleChange = vi.fn();
    render(<StylePanel style={BUILTIN_PRESETS.classic} aspect={16 / 9} onStyleChange={onStyleChange} />);

    fireEvent.click(screen.getByRole('switch', { name: t('subtitles.style.uppercase') }));
    expect(onStyleChange).toHaveBeenLastCalledWith({ ...BUILTIN_PRESETS.classic, uppercase: true });

    fireEvent.click(screen.getByRole('switch', { name: t('subtitles.style.pop') }));
    expect(onStyleChange).toHaveBeenLastCalledWith({ ...BUILTIN_PRESETS.classic, pop: true });
  });

  it('does not save a preset without a name', () => {
    render(<StylePanel style={BUILTIN_PRESETS.classic} aspect={16 / 9} onStyleChange={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: t('subtitles.style.saveAs') }));

    expect(settings.has('subtitles.presets')).toBe(false);
  });
});
