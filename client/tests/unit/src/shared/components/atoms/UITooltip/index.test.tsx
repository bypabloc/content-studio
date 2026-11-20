import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { UITooltip } from '@/shared/components/atoms/UITooltip';

function renderTooltip(shortcut?: string) {
  return render(
    <UITooltip content="Ocultar barra lateral" shortcut={shortcut}>
      <button type="button">Ocultar</button>
    </UITooltip>,
  );
}

describe('UITooltip', () => {
  it('aparece al pasar el ratón, tras la demora', async () => {
    const user = userEvent.setup();
    renderTooltip();

    await user.hover(screen.getByRole('button', { name: 'Ocultar' }));

    expect(screen.queryByRole('tooltip')).toBeNull();
    expect((await screen.findByRole('tooltip')).textContent).toContain('Ocultar barra lateral');
  });

  it('aparece al instante con el foco del teclado', async () => {
    const user = userEvent.setup();
    renderTooltip();

    await user.tab();

    await waitFor(() => expect(screen.getByRole('tooltip').textContent).toContain('Ocultar barra lateral'), {
      timeout: 150,
    });
  });

  it('se cierra con Escape', async () => {
    const user = userEvent.setup();
    renderTooltip();
    await user.tab();
    await screen.findByRole('tooltip');

    await user.keyboard('{Escape}');

    await waitFor(() => expect(screen.queryByRole('tooltip')).toBeNull());
  });

  it('muestra el atajo al lado del texto', async () => {
    const user = userEvent.setup();
    renderTooltip('Ctrl+B');
    await user.tab();

    const tooltip = await screen.findByRole('tooltip');

    expect(tooltip.textContent).toContain('Ctrl+B');
  });
});
