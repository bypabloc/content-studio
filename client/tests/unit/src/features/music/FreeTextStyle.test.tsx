import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { type FreeText, FreeTextStyle, freeTextComplete } from '@/features/music/FreeTextStyle';
import { t } from '@/shared/i18n/t';

const empty: FreeText = { caption: '', key: null, bpm: null, timeSignature: '4' };
const keys = ['C Major', 'D Minor'];

/** El formulario con su valor en estado, como en la pantalla. */
function Harness({ initial = empty, onChange }: { initial?: FreeText; onChange: (next: FreeText) => void }) {
  const [value, setValue] = useState(initial);
  return (
    <FreeTextStyle
      value={value}
      keys={keys}
      onChange={(next) => {
        setValue(next);
        onChange(next);
      }}
    />
  );
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('FreeTextStyle (spec 011, D-5, AC-7)', () => {
  it('WHEN falta el BPM THEN el texto libre no está completo y Generar queda deshabilitado', () => {
    expect(freeTextComplete({ caption: 'warm lofi', key: 'C Major', bpm: null, timeSignature: '4' })).toBe(false);
    expect(freeTextComplete({ caption: 'warm lofi', key: 'C Major', bpm: 80, timeSignature: '4' })).toBe(true);
  });

  it('WHEN se dan 4 toques de tap tempo cada 500 ms THEN el BPM queda en 120', () => {
    const onChange = vi.fn();
    // React también lee Date.now: el reloj devuelve la hora que la prueba fija antes de cada toque.
    let now = 0;
    vi.spyOn(Date, 'now').mockImplementation(() => now);
    render(<Harness onChange={onChange} />);
    const tap = screen.getByRole('button', { name: t('music.freeText.tap') });

    for (const at of [0, 500, 1000, 1500]) {
      now = at;
      fireEvent.click(tap);
    }

    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ bpm: 120 }));
  });

  it('WHEN se borra el BPM o no es entero THEN queda sin valor', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<Harness initial={{ ...empty, bpm: 80 }} onChange={onChange} />);
    const bpm = screen.getByRole('spinbutton', { name: t('music.freeText.bpm') });

    await user.clear(bpm);
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ bpm: null }));

    await user.type(bpm, '8.5');
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ bpm: null }));
  });

  it('WHEN se escribe la descripción THEN el texto libre la guarda', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<Harness onChange={onChange} />);

    await user.type(screen.getByRole('textbox', { name: t('music.freeText.caption') }), 'warm lofi');

    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ caption: 'warm lofi' }));
  });

  it('WHEN se elige la tonalidad D Minor THEN queda marcada y se guarda', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<Harness onChange={onChange} />);

    await user.click(screen.getByRole('button', { name: 'D Minor' }));

    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ key: 'D Minor' }));
    expect(screen.getByRole('button', { name: 'D Minor' }).getAttribute('aria-pressed')).toBe('true');
  });

  it('WHEN se elige el compás 6/8 THEN se guarda como 6', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<Harness onChange={onChange} />);

    await user.click(screen.getByRole('button', { name: '6/8' }));

    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ timeSignature: '6' }));
  });
});
