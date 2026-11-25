import { expect, test } from '@playwright/test';
import { apiFixture, openApp, type Call } from '../support/app';

test('AC-3: sin token, Instalar queda deshabilitado y no se encola la instalación', async ({ page }) => {
  const pyannote = {
    engine: 'pyannote', family: 'diarization', size_gb: 6, vram_gb: 2, cpu: true, license: 'MIT / CC-BY-4.0',
    commercial: true, status: 'missing', owner: null, gated: true, size_bytes: 0, job_id: null, verification: null,
  };
  const calls: Call[] = [];
  await openApp(page, {
    settings: { 'welcome.done': true },
    replies: (call) => {
      calls.push(call);
      if (call.method === 'GET' && call.path === '/engines') return [pyannote];
      if (call.method === 'GET' && call.path === '/system') return apiFixture('system/info');
      if (call.method === 'GET' && call.path === '/storage') return apiFixture('storage/paths');
      if (call.method === 'GET' && call.path === '/credentials/huggingface') return { configured: false };
      return undefined;
    },
  });
  await page.evaluate(() => {
    location.hash = '#/engines';
  });
  const card = page.locator('[id="engine-card-pyannote"]');
  await expect(card.getByLabel('Token de Hugging Face')).toBeVisible();
  await expect(card.getByRole('button', { name: 'Instalar', exact: true })).toBeDisabled();
  expect(calls.some((call) => call.method === 'POST' && call.path === '/engines/pyannote/install')).toBe(false);
});
