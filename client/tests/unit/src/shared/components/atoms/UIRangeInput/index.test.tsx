import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { UIRangeInput } from '@/shared/components/atoms/UIRangeInput';

describe('UIRangeInput', () => {
  it('nombra el control y devuelve el valor numérico', () => {
    const onValueChange = vi.fn();
    render(<UIRangeInput label="Volumen de voz" min={-60} max={12} step={1} value={0} onValueChange={onValueChange} />);

    const input = screen.getByRole('slider', { name: 'Volumen de voz' });
    expect(input.getAttribute('min')).toBe('-60');
    expect(input.getAttribute('max')).toBe('12');
    fireEvent.change(input, { target: { value: '-6' } });

    expect(onValueChange).toHaveBeenCalledWith(-6);
  });
});
