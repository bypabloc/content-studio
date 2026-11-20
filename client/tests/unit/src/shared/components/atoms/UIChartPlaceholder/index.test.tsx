import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { UIChartPlaceholder } from '@/shared/components/atoms/UIChartPlaceholder';

describe('UIChartPlaceholder', () => {
  it('reserva la altura de la gráfica con el atributo height, sin prop style', () => {
    const { container } = render(<UIChartPlaceholder height={240} />);

    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('height')).toBe('240');
    expect(svg?.getAttribute('aria-hidden')).toBe('true');
    expect(svg?.getAttribute('data-slot')).toBe('chart-placeholder');
    expect(svg?.getAttribute('style')).toBeNull();
  });
});
