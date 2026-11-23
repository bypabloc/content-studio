import { createRef } from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { UICanvas } from '@/shared/components/atoms/UICanvas';

describe('UICanvas', () => {
  it('expone un canvas accesible y reenvia su referencia', () => {
    const canvasRef = createRef<HTMLCanvasElement>();
    render(<UICanvas ref={canvasRef} aria-label="Vista previa" width={640} height={360} />);

    const canvas = screen.getByLabelText('Vista previa');
    expect(canvas.tagName).toBe('CANVAS');
    expect(canvasRef.current).toBe(canvas);
    expect(canvas.getAttribute('width')).toBe('640');
    expect(canvas.getAttribute('height')).toBe('360');
  });
});
