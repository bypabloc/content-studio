import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { CommandPalette } from '@/app/CommandPalette';
import { NAV } from '@/app/nav';
import { t } from '@/shared/i18n/t';

afterEach(() => {
  cleanup();
  window.location.hash = '';
});

function open() {
  fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
  return screen.getByRole('combobox');
}

describe('CommandPalette', () => {
  it('Ctrl+K la abre y escribir filtra las secciones sin distinguir tildes', () => {
    render(<CommandPalette items={NAV} />);
    expect(screen.queryByRole('dialog')).toBeNull();

    const input = open();
    fireEvent.change(input, { target: { value: 'ajus' } });

    expect(screen.getByRole('dialog')).toBeTruthy();
    expect(screen.getByRole('option', { name: 'Ajustes' })).toBeTruthy();
  });

  it('una búsqueda sin resultados lo dice', () => {
    render(<CommandPalette items={NAV} />);

    fireEvent.change(open(), { target: { value: 'zzz' } });

    expect(screen.getByText(t('palette.empty'))).toBeTruthy();
  });

  it('Enter navega a la sección elegida y cierra la paleta', () => {
    render(<CommandPalette items={NAV} />);
    const input = open();
    fireEvent.change(input, { target: { value: 'ajus' } });

    fireEvent.keyDown(input, { key: 'Enter' });

    expect(window.location.hash).toBe('#/settings');
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('las flechas mueven la selección y el clic navega a la sección', () => {
    const two = [
      { id: 'alfa', group: 'G', label: 'Alfa' },
      { id: 'beta', group: 'G', label: 'Beta' },
    ];
    render(<CommandPalette items={two} />);
    const input = open();

    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'ArrowUp' });
    expect(screen.getByRole('option', { name: 'Alfa' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.click(screen.getByRole('option', { name: 'Beta' }));

    expect(window.location.hash).toBe('#/beta');
  });

  it('Escape cierra la paleta sin navegar', () => {
    render(<CommandPalette items={NAV} />);
    const input = open();

    fireEvent.keyDown(input, { key: 'Escape' });

    expect(screen.queryByRole('dialog')).toBeNull();
    expect(window.location.hash).toBe('');
  });
});
