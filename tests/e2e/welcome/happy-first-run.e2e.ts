import { expect, test } from '@playwright/test';
import { apiFixture, openApp, type Call } from '../support/app';

test('AC-8: completar la bienvenida sin descargar el paquete recomendado', async ({ page }) => {
  const calls: Call[] = [];
  await openApp(page, {
    settings: { 'welcome.done': null },
    replies: (call) => {
      calls.push(call);
      if (call.method === 'GET' && call.path === '/engines') return apiFixture('engines/onboarding');
      if (call.method === 'GET' && call.path === '/system') return apiFixture('system/missing-ffmpeg');
      if (call.method === 'GET' && call.path === '/storage') return apiFixture('storage/paths');
      return undefined;
    },
  });

  await page.getByRole('dialog', { name: 'Bienvenida a Content Studio' }).waitFor();
  await page.getByRole('button', { name: 'Siguiente' }).click();
  await page.getByRole('button', { name: 'Siguiente' }).click();
  await page.getByRole('checkbox', { name: 'voxcpm2' }).uncheck();
  await page.getByRole('checkbox', { name: 'acestep' }).uncheck();
  await page.getByRole('button', { name: 'Siguiente' }).click();
  await page.getByRole('button', { name: 'Agregar a la cola e ir a Narración' }).click();

  await expect.poll(() => calls.some((call) =>
    call.method === 'PUT' && call.path === '/settings/welcome.done' && (call.body as { value?: unknown }).value === true,
  )).toBe(true);
  expect(calls.some((call) => call.method === 'POST' && call.path.includes('/engines/'))).toBe(false);
});
