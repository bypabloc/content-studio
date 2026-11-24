import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';

describe('UIIconButton', () => {
  it('se nombra con aria-label y su ícono queda oculto a lectores de pantalla', () => {
    const { container } = render(<UIIconButton icon="search" label="Buscar" />);

    expect(screen.getByRole('button', { name: 'Buscar' })).toBeTruthy();
    expect(container.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true');
  });

  it('con pressed expone aria-pressed; sin pressed no lo pone', () => {
    const { unmount } = render(<UIIconButton icon="eye" label="Mostrar" pressed />);
    expect(screen.getByRole('button', { name: 'Mostrar' }).getAttribute('aria-pressed')).toBe('true');
    unmount();

    render(<UIIconButton icon="eye" label="Mostrar" />);
    expect(screen.getByRole('button', { name: 'Mostrar' }).getAttribute('aria-pressed')).toBeNull();
  });

  it('llama a onClick al pulsar', async () => {
    const onClick = vi.fn();
    render(<UIIconButton icon="send" label="Enviar" onClick={onClick} />);

    await userEvent.click(screen.getByRole('button', { name: 'Enviar' }));

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('muestra el texto de ayuda al enfocarlo, con el atajo si lo tiene', async () => {
    render(<UIIconButton icon="search" label="Buscar" shortcut="Ctrl+K" />);

    await userEvent.tab();

    const tooltip = await screen.findByRole('tooltip');
    expect(tooltip.textContent).toContain('Buscar');
    expect(tooltip.textContent).toContain('Ctrl+K');
  });
});
