import { expect, test } from '@playwright/test';
import { apiFixture, openApp, type Call } from '../support/app';

test('AC-6: avisar que falta FFmpeg y ofrecer su instalación', async ({ page }) => {
  const calls: Call[] = [];
  await openApp(page, {
    settings: { 'welcome.done': true },
    replies: (call) => {
      calls.push(call);
      if (call.method === 'GET' && call.path === '/engines') return apiFixture('engines/qwen-external');
      if (call.method === 'GET' && call.path === '/system') return apiFixture('system/missing-ffmpeg');
      if (call.method === 'GET' && call.path === '/storage') return apiFixture('storage/paths');
      return undefined;
    },
  });

  await expect(page.getByText(/FFmpeg no está disponible en el PATH/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Instalar FFmpeg' })).toBeVisible();
  await page.getByRole('button', { name: 'Instalar FFmpeg' }).click();
  await expect.poll(() => calls.some((call) =>
    call.method === 'POST' && call.path === '/system/tools/ffmpeg/install',
  )).toBe(true);
});
