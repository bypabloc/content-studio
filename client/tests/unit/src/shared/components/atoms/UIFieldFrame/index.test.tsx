import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { UIFieldFrame } from '@/shared/components/atoms/UIFieldFrame';

describe('UIFieldFrame', () => {
  it('asocia el texto visible al control por htmlFor', () => {
    render(
      <UIFieldFrame label="Correo" htmlFor="mail">
        <input id="mail" />
      </UIFieldFrame>,
    );

    expect(screen.getByLabelText('Correo').id).toBe('mail');
  });

  it('con hideLabel oculta el texto visible, pero sigue siendo el nombre del control', () => {
    render(
      <UIFieldFrame label="Buscar" htmlFor="q" hideLabel>
        <input id="q" />
      </UIFieldFrame>,
    );

    expect(screen.getByText('Buscar').className).toContain('sr-only');
    expect(screen.getByLabelText('Buscar').id).toBe('q');
  });

  it('muestra el error tras el control, con su ícono y el id que lo describe', () => {
    const { container } = render(
      <UIFieldFrame label="Correo" htmlFor="mail" error="Falta el correo" errorId="mail-error">
        <input id="mail" />
      </UIFieldFrame>,
    );

    const error = document.getElementById('mail-error') as Node;
    expect(error.textContent).toContain('Falta el correo');
    expect(container.querySelector('svg')).not.toBeNull();
    const input = container.querySelector('#mail') as Node;
    expect(input.compareDocumentPosition(error) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('muestra la pista después del error', () => {
    render(
      <UIFieldFrame label="Clave" htmlFor="pwd" error="Corta" errorId="pwd-error" hint="Mínimo 8" hintId="pwd-hint">
        <input id="pwd" />
      </UIFieldFrame>,
    );

    const error = document.getElementById('pwd-error') as Node;
    const hint = document.getElementById('pwd-hint') as Node;
    expect(error.compareDocumentPosition(hint) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('sin error ni pista no pinta ningún ícono', () => {
    const { container } = render(
      <UIFieldFrame label="Nombre" htmlFor="n">
        <input id="n" />
      </UIFieldFrame>,
    );

    expect(container.querySelector('svg')).toBeNull();
  });
});
