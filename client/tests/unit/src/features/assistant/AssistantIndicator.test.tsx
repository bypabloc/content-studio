import { cleanup, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { AssistantIndicator } from '@/features/assistant/AssistantIndicator';
import { t } from '@/shared/i18n/t';

import { api, renderWith, STATUS } from '../../../assistant-harness';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('AssistantIndicator (spec 021, D-2)', () => {
  it('WHEN hay un modelo caliente THEN dice cuál y en cuánto se libera la GPU', async () => {
    renderWith(<AssistantIndicator />, api({ '/llm/status': { ...STATUS, loaded: 'qwen3.5-9b', release_in: 105 } }));
    expect(await screen.findByText(t('llm.loaded', { model: 'qwen3.5-9b', time: '1:45' }))).toBeTruthy();
  });

  it('WHEN todavía no hay cuenta regresiva THEN muestra 0:00', async () => {
    renderWith(<AssistantIndicator />, api({ '/llm/status': { ...STATUS, loaded: 'gemma-4-e4b', release_in: null } }));
    expect(await screen.findByText(t('llm.loaded', { model: 'gemma-4-e4b', time: '0:00' }))).toBeTruthy();
  });

  it('WHEN no hay modelo cargado THEN no muestra nada', async () => {
    const { container } = renderWith(<AssistantIndicator />, api({ '/llm/status': STATUS }));
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(container.textContent).toBe('');
  });
});
