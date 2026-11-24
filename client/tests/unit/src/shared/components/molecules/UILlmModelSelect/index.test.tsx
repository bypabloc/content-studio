import { cleanup, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { UILlmModelSelect } from '@/shared/components/molecules/UILlmModelSelect';
import { t } from '@/shared/i18n/t';

import { api, renderWith, STATUS } from '../../../../../assistant-harness';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('UILlmModelSelect (spec 021, D-5)', () => {
  it('WHEN se abre THEN lista los modelos con ★ en el recomendado y si están instalados', async () => {
    const models = [...STATUS.models, { model: 'qwen3.5-9b', size_gb: 5.7, vram_gb: 7, recommended: false, installed: false }];
    renderWith(<UILlmModelSelect />, api({ '/llm/status': { ...STATUS, models }, '/settings/select.llm.model': { key: 'k', value: null } }));

    await userEvent.click(await screen.findByRole('combobox', { name: t('llm.settings.model') }));

    expect(await screen.findByRole('option', { name: /gemma-4-e4b/ })).toBeTruthy();
    expect(screen.getByRole('option', { name: /qwen3\.5-9b/ }).textContent).toContain(t('llm.model.missing'));
  });
});
