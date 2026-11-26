import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';

const FRAGMENTS: Record<string, string> = {
  'claude-code': '{"mcpServers": {"content-studio": {"command": "studio", "args": ["mcp"]}}}',
  codex: '[mcp_servers.content-studio]\ncommand = "studio"\nargs = ["mcp"]\n',
};

test('Ajustes > Integraciones: al elegir Codex, «Copiar configuración» copia su fragmento (AC-10)', async ({ page }) => {
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);
  await openApp(page, {
    replies: (call) => {
      if (call.path !== '/integrations/mcp-config') return undefined;
      const client = new URLSearchParams(call.search).get('client') ?? '';
      return { client, fragment: FRAGMENTS[client] };
    },
  });
  await page.evaluate(() => {
    location.hash = '#/settings';
  });

  await page.getByRole('combobox', { name: 'Aplicación' }).click();
  await page.getByRole('option', { name: 'Codex' }).click();
  await page.getByRole('button', { name: 'Copiar configuración' }).click();

  // Windows convierte los saltos de línea del portapapeles a CRLF: se comparan sin ellos.
  await expect.poll(() => page.evaluate(() => navigator.clipboard.readText()).then((text) => text.replace(/\r\n/g, '\n'))).toBe(FRAGMENTS.codex);
});
