import { act, cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { Sidebar } from '@/app/Sidebar';
import { NAV } from '@/app/nav';

const items = [
  { id: 'narration', group: 'Generar', label: 'Narración' },
  { id: 'music', group: 'Generar', label: 'Música' },
  { id: 'voices', group: 'Voces', label: 'Voces' },
];

afterEach(() => {
  cleanup();
  window.location.hash = '';
});

describe('Sidebar', () => {
  it('agrupa las entradas por grupo y cada una enlaza a su sección', () => {
    render(<Sidebar items={items} />);

    expect(screen.getByRole('heading', { name: 'Generar' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Voces' })).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Narración' }).getAttribute('href')).toBe('#/narration');
  });

  it('marca la sección activa y la sigue cuando cambia el hash', () => {
    window.location.hash = '#/music';
    render(<Sidebar items={items} />);
    expect(screen.getByRole('link', { name: 'Música' }).getAttribute('aria-current')).toBe('page');

    act(() => {
      window.location.hash = '#/voices';
      window.dispatchEvent(new HashChangeEvent('hashchange'));
    });

    expect(screen.getByRole('link', { name: 'Voces' }).getAttribute('aria-current')).toBe('page');
    expect(screen.getByRole('link', { name: 'Música' }).getAttribute('aria-current')).toBeNull();
  });

  it('sin items dados, el menú sale de nav.ts', () => {
    render(<Sidebar />);

    for (const item of NAV) expect(screen.getByRole('link', { name: item.label })).toBeTruthy();
  });
});
