import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';

test('Ajustes > Integraciones: si la API no arma la configuración, avisa y no ofrece copiar (AC-10)', async ({ page }) => {
  await openApp(page, {
    replies: (call) =>
      call.path === '/integrations/mcp-config' ? { failed: { status: 500, body: { code: 'internal' } } } : undefined,
  });
  await page.evaluate(() => {
    location.hash = '#/settings';
  });

  await expect(page.getByText('No se pudo preparar la configuración. Revisa que el server esté activo.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Copiar configuración' })).toHaveCount(0);
});
