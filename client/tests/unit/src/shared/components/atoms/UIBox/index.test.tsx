import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { UIBox } from '@/shared/components/atoms/UIBox';

describe('UIBox', () => {
  it('es un div por defecto', () => {
    render(<UIBox data-testid="caja">contenido</UIBox>);

    expect(screen.getByTestId('caja').tagName).toBe('DIV');
  });

  it('cambia la etiqueta con `as`: nav, aside, main, footer…', () => {
    render(
      <UIBox as="nav" data-testid="caja">
        <span>enlace</span>
      </UIBox>,
    );

    expect(screen.getByTestId('caja').tagName).toBe('NAV');
    expect(screen.getByText('enlace')).toBeTruthy();
  });

  it('aplica su className junto a las clases del componente', () => {
    render(
      <UIBox className="flex gap-2" data-testid="caja">
        x
      </UIBox>,
    );

    expect(screen.getByTestId('caja').classList.contains('flex')).toBe(true);
    expect(screen.getByTestId('caja').classList.contains('gap-2')).toBe(true);
  });

  it('pasa los demás atributos al elemento (aria-label, id)', () => {
    render(
      <UIBox as="aside" aria-label="Panel" id="panel">
        x
      </UIBox>,
    );

    expect(screen.getByRole('complementary', { name: 'Panel' }).getAttribute('id')).toBe('panel');
  });
});
