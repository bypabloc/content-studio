import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIStack } from '@/shared/components/atoms/UIStack'

describe('UIStack', () => {
  it('stacks in a column with the requested spacing', () => {
    const { container } = render(<UIStack gap="lg">a</UIStack>)

    expect(container.firstElementChild?.className).toContain('gap-6')
  })

  it('admite el espaciado xs (gap-1), el que usan las filas de tomas', () => {
    const { container } = render(<UIStack gap="xs">a</UIStack>)

    expect(container.firstElementChild?.className).toContain('gap-1')
  })

  it('uses medium spacing by default', () => {
    const { container } = render(<UIStack>a</UIStack>)

    expect(container.firstElementChild?.className).toContain('gap-4')
  })
})

describe('UIStack: dirección y alineación (spec 008, D-3)', () => {
  it('va en fila con direction="row" y en columna por defecto', () => {
    render(
      <>
        <UIStack data-testid="fila" direction="row">
          x
        </UIStack>
        <UIStack data-testid="columna">x</UIStack>
      </>,
    );

    expect(screen.getByTestId('fila').classList.contains('flex-row')).toBe(true);
    expect(screen.getByTestId('columna').classList.contains('flex-col')).toBe(true);
  });

  it('alinea con align y reparte con justify', () => {
    render(
      <UIStack data-testid="caja" direction="row" align="center" justify="between">
        x
      </UIStack>,
    );

    expect(screen.getByTestId('caja').classList.contains('items-center')).toBe(true);
    expect(screen.getByTestId('caja').classList.contains('justify-between')).toBe(true);
  });
});

