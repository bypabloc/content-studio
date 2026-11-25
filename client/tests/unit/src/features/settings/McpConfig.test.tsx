import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { McpConfig } from '@/features/settings/McpConfig';
import type { Connection } from '@/shared/api/client';
import { ApiProvider } from '@/shared/api/context';
import { t } from '@/shared/i18n/t';

const connection: Connection = { baseUrl: 'http://127.0.0.1:41830', token: 'tok' };
const FRAGMENTS: Record<string, string> = {
  'claude-code': '{"mcpServers": {"content-studio": {"command": "studio", "args": ["mcp"]}}}',
  codex: '[mcp_servers.content-studio]\ncommand = "studio"\nargs = ["mcp"]\n',
};

/** Responde a GET /integrations/mcp-config?client=<c> con el fragmento de ese cliente. */
function configFetch(fail = false) {
  return vi.fn(async (url: string) => {
    if (fail) return new Response(JSON.stringify({ code: 'internal' }), { status: 500 });
    const client = new URL(url).searchParams.get('client') ?? '';
    return new Response(JSON.stringify({ client, fragment: FRAGMENTS[client] }), { status: 200 });
  });
}

function renderConfig(fail = false) {
  vi.stubGlobal('fetch', configFetch(fail));
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ApiProvider connection={connection}>{children}</ApiProvider>
    </QueryClientProvider>
  );
  render(<McpConfig />, { wrapper });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('McpConfig (spec 029, AC-10)', () => {
  it('al elegir Codex, «Copiar configuración» copia el fragmento de la API', async () => {
    const writeText = vi.fn(async () => undefined);
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
    renderConfig();

    await userEvent.click(await screen.findByRole('combobox', { name: t('settings.integrations.mcp_client') }));
    await userEvent.click(await screen.findByRole('option', { name: 'Codex' }));

    const copy = (await screen.findByRole('button', { name: t('settings.integrations.mcp_copy') })) as HTMLButtonElement;
    await waitFor(() => expect(copy.disabled).toBe(false));
    await userEvent.click(copy);

    expect(writeText).toHaveBeenCalledWith(FRAGMENTS.codex);
  });

  it('si la API no arma la configuración, avisa y no ofrece copiar', async () => {
    renderConfig(true);

    expect(await screen.findByText(t('settings.integrations.mcp_failed'))).toBeTruthy();
    expect(screen.queryByRole('button', { name: t('settings.integrations.mcp_copy') })).toBeNull();
  });
});
