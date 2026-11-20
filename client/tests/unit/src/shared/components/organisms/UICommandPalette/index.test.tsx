import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { UICommandPalette } from '@/shared/components/organisms/UICommandPalette';

// Los ítems llegan por props: la paleta no sabe de secciones, solo de lo que le pasan (spec 008, D-3).
const LABELS = { title: 'Ir a una sección', placeholder: 'Buscar sección…', empty: 'Sin resultados' };

const ITEMS = [
  { id: 'narration', label: 'Narración' },
  { id: 'settings', label: 'Ajustes' },
];

afterEach(() => {
  cleanup();
});

function open() {
  fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
  return screen.getByRole('combobox');
}

describe('UICommandPalette', () => {
  it('Ctrl+K la abre y escribir filtra las secciones sin distinguir tildes', () => {
    render(<UICommandPalette items={ITEMS} onSelect={vi.fn()} labels={LABELS} />);
    expect(screen.queryByRole('dialog')).toBeNull();

    const input = open();
    fireEvent.change(input, { target: { value: 'ajus' } });

    expect(screen.getByRole('dialog')).toBeTruthy();
    expect(screen.getByRole('option', { name: 'Ajustes' })).toBeTruthy();
  });

  it('una búsqueda sin resultados lo dice', () => {
    render(<UICommandPalette items={ITEMS} onSelect={vi.fn()} labels={LABELS} />);

    fireEvent.change(open(), { target: { value: 'zzz' } });

    expect(screen.getByText(LABELS.empty)).toBeTruthy();
  });

  it('Enter elige la sección con su id y cierra la paleta', () => {
    const onSelect = vi.fn();
    render(<UICommandPalette items={ITEMS} onSelect={onSelect} labels={LABELS} />);
    const input = open();
    fireEvent.change(input, { target: { value: 'ajus' } });

    fireEvent.keyDown(input, { key: 'Enter' });

    expect(onSelect).toHaveBeenCalledWith('settings');
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('las flechas mueven la selección y el clic elige la sección', () => {
    const onSelect = vi.fn();
    const two = [
      { id: 'alfa', label: 'Alfa' },
      { id: 'beta', label: 'Beta' },
    ];
    render(<UICommandPalette items={two} onSelect={onSelect} labels={LABELS} />);
    const input = open();

    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'ArrowUp' });
    expect(screen.getByRole('option', { name: 'Alfa' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.click(screen.getByRole('option', { name: 'Beta' }));

    expect(onSelect).toHaveBeenCalledWith('beta');
  });

  it('Escape cierra la paleta sin elegir nada', () => {
    const onSelect = vi.fn();
    render(<UICommandPalette items={ITEMS} onSelect={onSelect} labels={LABELS} />);
    const input = open();

    fireEvent.keyDown(input, { key: 'Escape' });

    expect(screen.queryByRole('dialog')).toBeNull();
    expect(onSelect).not.toHaveBeenCalled();
  });
});
