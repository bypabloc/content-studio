import { render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { UICanvas } from '@/shared/components/atoms/UICanvas';

describe('UICanvas', () => {
  it('renders a canvas with its dimensions and ref', () => {
    const ref = vi.fn();
    const { container } = render(<UICanvas ref={ref} width={320} height={180} aria-hidden="true" />);
    const canvas = container.querySelector('canvas');

    expect(canvas).not.toBeNull();
    expect(canvas?.width).toBe(320);
    expect(canvas?.height).toBe(180);
    expect(ref).toHaveBeenCalledWith(canvas);
  });
});
