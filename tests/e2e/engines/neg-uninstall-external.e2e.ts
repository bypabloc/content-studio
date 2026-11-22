import { expect, test } from '@playwright/test';
import { apiFixture, openApp, type Call } from '../support/app';

test('AC-5: un motor externo no se desinstala sin escribir su nombre', async ({ page }) => {
  const calls: Call[] = [];
  await openApp(page, {
    settings: { 'welcome.done': true },
    replies: (call) => {
      calls.push(call);
      if (call.method === 'GET' && call.path === '/engines') return apiFixture('engines/qwen-external');
      if (call.method === 'GET' && call.path === '/system') return apiFixture('system/info');
      if (call.method === 'GET' && call.path === '/storage') return apiFixture('storage/paths');
      return undefined;
    },
  });

  await page.evaluate(() => { location.hash = '#/engines'; });
  const card = page.locator('[id="engine-card-qwen-0.6b"]');
  await card.getByRole('button', { name: 'Desinstalar', exact: true }).click();
  await expect(card.getByLabel('Escribe el nombre del motor')).toBeVisible();
  await expect(card.getByRole('button', { name: 'Confirmar desinstalación' })).toBeDisabled();
  expect(calls.some((call) => call.method === 'POST' && call.path.includes('/uninstall'))).toBe(false);
});
