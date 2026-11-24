import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { UIVirtualList } from '@/shared/components/molecules/UIVirtualList';

afterEach(() => cleanup());

describe('UIVirtualList (spec 020, AC-9)', () => {
  it('con muchas filas solo pone en el DOM las visibles y un margen', () => {
    render(<UIVirtualList label="filas" count={1000} rowHeight={40} height={400} renderRow={(index) => `fila ${index}`} />);

    const rows = screen.getAllByRole('listitem');
    expect(screen.getByRole('list', { name: 'filas' })).toBeTruthy();
    expect(rows.length).toBeGreaterThanOrEqual(10);
    expect(rows.length).toBeLessThan(40);
    expect(rows[0].textContent).toBe('fila 0');
  });

  it('sin filas no dibuja ninguna', () => {
    render(<UIVirtualList label="vacía" count={0} rowHeight={40} height={400} renderRow={() => 'x'} />);

    expect(screen.queryAllByRole('listitem')).toHaveLength(0);
  });

  it('usa el alto medido del contenedor cuando lo hay', () => {
    const rect = vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({ width: 300, height: 80 } as DOMRect);

    render(<UIVirtualList label="medida" count={1000} rowHeight={40} height={400} renderRow={(index) => `fila ${index}`} />);

    expect(screen.getAllByRole('listitem').length).toBeLessThan(15);
    rect.mockRestore();
  });

});
