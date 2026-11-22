import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { UIErrorDetailDialog } from '@/shared/components/organisms/UIErrorDetailDialog';

describe('UIErrorDetailDialog', () => {
  it('muestra el mensaje amigable y el detalle técnico dentro de un diálogo con título', () => {
    render(
      <UIErrorDetailDialog
        open
        onOpenChange={vi.fn()}
        title="No se pudo convertir"
        message="Este ffmpeg no trae el codificador libopus."
        detail="Unknown encoder 'libopus'"
        closeLabel="Cerrar"
      />,
    );

    const dialog = screen.getByRole('dialog', { name: 'No se pudo convertir' });
    expect(dialog.textContent).toContain('Este ffmpeg no trae el codificador libopus.');
    expect(dialog.textContent).toContain("Unknown encoder 'libopus'");
  });

  it('no muestra nada cuando está cerrado', () => {
    render(
      <UIErrorDetailDialog
        open={false}
        onOpenChange={vi.fn()}
        title="No se pudo convertir"
        message="x"
        closeLabel="Cerrar"
      />,
    );

    expect(screen.queryByRole('dialog')).toBeNull();
  });
});
