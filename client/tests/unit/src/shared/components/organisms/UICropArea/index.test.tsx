import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { type CropRect, UICropArea } from '@/shared/components/organisms/UICropArea';

const rect: CropRect = { x: 0.2, y: 0, w: 0.4, h: 1 };

function renderArea(onChange = vi.fn()) {
  render(
    <UICropArea
      label="Encuadre del cuadro"
      src="http://test/media/frame"
      alt="Cuadro de la fuente"
      width={1920}
      height={1080}
      rect={rect}
      onChange={onChange}
      errorText="No se pudo cargar"
      retryLabel="Reintentar"
    />,
  );
  return onChange;
}

describe('UICropArea', () => {
  beforeEach(() => {
    // La zona mide 400 x 300 px: el arrastre se mide en fracciones de ese tamaño.
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      left: 0,
      top: 0,
      right: 400,
      bottom: 300,
      width: 400,
      height: 300,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    } as DOMRect);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('el rectángulo se pone en sus coordenadas normalizadas', () => {
    renderArea();

    const crop = screen.getByTestId('crop-rect');
    expect(crop.style.left).toBe('20%');
    expect(crop.style.width).toBe('40%');
    expect(crop.style.height).toBe('100%');
  });

  it('arrastrar lo mueve dentro del cuadro y no lo deja salirse', () => {
    const onChange = renderArea();
    const area = screen.getByRole('group', { name: 'Encuadre del cuadro' });

    fireEvent.pointerDown(screen.getByTestId('crop-rect'), { clientX: 100, clientY: 100, pointerId: 1 });
    fireEvent.pointerMove(area, { clientX: 1000, clientY: 100, pointerId: 1 });

    // Sin tope, x sería 0,2 + 900/400 = 2,45. El cuadro de 0,4 de ancho llega como mucho a x = 0,6.
    expect(onChange.mock.lastCall?.[0]).toMatchObject({ x: 0.6, y: 0, w: 0.4, h: 1 });
  });

  it('soltar el puntero deja de mover el rectángulo', () => {
    const onChange = renderArea();
    const area = screen.getByRole('group', { name: 'Encuadre del cuadro' });

    fireEvent.pointerDown(screen.getByTestId('crop-rect'), { clientX: 100, clientY: 100, pointerId: 1 });
    fireEvent.pointerUp(area, { clientX: 100, clientY: 100, pointerId: 1 });
    fireEvent.pointerMove(area, { clientX: 140, clientY: 100, pointerId: 1 });

    expect(onChange).not.toHaveBeenCalled();
  });
});
