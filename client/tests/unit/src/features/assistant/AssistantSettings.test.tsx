import { cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { AssistantSettings } from '@/features/assistant/AssistantSettings';
import { t } from '@/shared/i18n/t';

import { api, calls, renderWith, STATUS } from '../../../assistant-harness';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const settings = (body: unknown) => body;

describe('AssistantSettings (spec 021, D-5)', () => {
  it('WHEN se apaga el asistente y se cambia la espera THEN guarda llm.enabled y llm.idle_seconds', async () => {
    const fetchMock = api({
      '/llm/status': STATUS,
      '/settings/llm.enabled': { key: 'llm.enabled', value: null },
      '/settings/llm.idle_seconds': { key: 'llm.idle_seconds', value: null },
      '/settings/select.llm.model': { key: 'select.llm.model', value: null },
      'PUT /settings/llm.enabled': settings,
      'PUT /settings/llm.idle_seconds': settings,
    });
    renderWith(<AssistantSettings />, fetchMock);

    await userEvent.click(await screen.findByRole('checkbox', { name: t('llm.settings.enabled') }));
    await userEvent.click(screen.getByRole('combobox', { name: t('llm.settings.idle') }));
    await userEvent.click(await screen.findByRole('option', { name: t('llm.settings.idle_option', { minutes: 5 }) }));

    await waitFor(() => expect(calls(fetchMock)).toContain('PUT /settings/llm.idle_seconds'));
    const bodies = fetchMock.mock.calls.filter(([, init]) => init?.method === 'PUT').map(([, init]) => String(init?.body));
    expect(bodies).toContain('{"value":false}');
    expect(bodies).toContain('{"value":300}');
  });
});
