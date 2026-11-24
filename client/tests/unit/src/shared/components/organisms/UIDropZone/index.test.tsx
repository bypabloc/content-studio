import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { UIDropZone } from '@/shared/components/organisms/UIDropZone';

describe('UIDropZone', () => {
  it('muestra el título, la pista y el botón que abre el diálogo del sistema', () => {
    const onPick = vi.fn();
    render(
      <UIDropZone dragging={false} title="Suelta aquí los archivos" hint="Audio o video" actionLabel="Elegir archivos" onPick={onPick} />,
    );

    expect(screen.getByText('Suelta aquí los archivos')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Elegir archivos' }));
    expect(onPick).toHaveBeenCalledOnce();
  });

  it('se marca mientras hay archivos sobre la ventana', () => {
    const { container, rerender } = render(
      <UIDropZone dragging={false} title="t" hint="h" actionLabel="a" onPick={vi.fn()} />,
    );
    expect(container.querySelector('[data-dragging="true"]')).toBeNull();

    rerender(<UIDropZone dragging title="t" hint="h" actionLabel="a" onPick={vi.fn()} />);
    expect(container.querySelector('[data-dragging="true"]')).not.toBeNull();
  });
});
