import { cleanup, fireEvent, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { AssistantButton } from '@/features/assistant/AssistantButton';
import { t } from '@/shared/i18n/t';

import { api, renderWith, STATUS } from '../../../assistant-harness';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('AssistantButton (spec 021, AC-9)', () => {
  it('WHEN el asistente está apagado en Ajustes THEN el botón no aparece', async () => {
    const { container } = renderWith(<AssistantButton label="Revisar" busy={false} error={null} onClick={() => {}} />, api({ '/llm/status': { ...STATUS, enabled: false } }));
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(container.textContent).toBe('');
  });

  it('WHEN falta el modelo THEN lleva a Motores', async () => {
    renderWith(<AssistantButton label="Revisar" busy={false} error={null} onClick={() => {}} />, api({ '/llm/status': { ...STATUS, runtime_installed: false } }));
    const link = await screen.findByRole('link', { name: t('llm.install') });
    expect(link.getAttribute('href')).toBe('#/engines?engine=llama-cpp');
  });

  it('WHEN está listo THEN corre la tarea; ocupado dice que carga y muestra el error', async () => {
    const onClick = vi.fn();
    const view = renderWith(<AssistantButton label="Revisar" busy={false} error={null} onClick={onClick} />, api({ '/llm/status': STATUS }));
    fireEvent.click(await screen.findByRole('button', { name: 'Revisar' }));
    expect(onClick).toHaveBeenCalled();

    view.rerender(<AssistantButton label="Revisar" busy error="llm_timeout" onClick={onClick} />);
    expect(screen.getByRole('button', { name: t('llm.loading') }).hasAttribute('disabled')).toBe(true);
    expect(screen.getByText(t('error.llm_timeout'))).toBeTruthy();
  });
});
