import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { UILevelMeter } from '@/shared/components/atoms/UILevelMeter';

afterEach(() => {
  cleanup();
});

describe('UILevelMeter (spec 010, D-2)', () => {
  it('expone el nivel RMS como medidor con su nombre y su valor en dBFS', () => {
    render(<UILevelMeter label="Nivel" rms={-18} peak={-3} zone={[-12, -6]} alertAbove={-1} />);

    const meter = screen.getByRole('meter', { name: 'Nivel' });
    expect(meter.getAttribute('aria-valuenow')).toBe('-18');
    expect(meter.getAttribute('aria-valuetext')).toBe('-18.0 dBFS');
  });

  it('un nivel por debajo del piso se queda en el piso, sin salirse del medidor', () => {
    render(<UILevelMeter label="Nivel" rms={-120} peak={-120} zone={[-12, -6]} alertAbove={-1} />);

    const meter = screen.getByRole('meter', { name: 'Nivel' });
    expect(meter.getAttribute('aria-valuenow')).toBe('-120');
  });
});
