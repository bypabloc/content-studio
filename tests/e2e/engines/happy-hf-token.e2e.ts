import { expect, test } from '@playwright/test';
import { apiFixture, openApp, type Call } from '../support/app';

const TOKEN = 'hf_' + 'a'.repeat(34);

test('AC-5: guardar el token de Hugging Face habilita Instalar en la tarjeta de pyannote', async ({ page }) => {
  let saved = false;
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
      if (call.method === 'GET' && call.path === '/credentials/huggingface') return { configured: saved };
      if (call.method === 'PUT' && call.path === '/credentials/huggingface') {
        saved = true;
        return { configured: true };
      }
      if (call.method === 'DELETE' && call.path === '/credentials/huggingface') {
        saved = false;
        return { configured: false };
      }
      return undefined;
    },
  });
  await page.evaluate(() => {
    location.hash = '#/engines';
  });
  const card = page.locator('[id="engine-card-pyannote"]');
  const install = card.getByRole('button', { name: 'Instalar', exact: true });
  await expect(install).toBeDisabled();

  await card.getByLabel('Token de Hugging Face').fill(TOKEN);
  await card.getByRole('button', { name: 'Guardar token', exact: true }).click();
  await expect(card.getByText('Token guardado')).toBeVisible();
  await expect(install).toBeEnabled();

  await card.getByRole('button', { name: 'Quitar', exact: true }).click();
  await expect(card.getByLabel('Token de Hugging Face')).toBeVisible();
  expect(
    calls.some((call) => call.method === 'PUT' && call.path === '/credentials/huggingface' && (call.body as { token?: string })?.token === TOKEN),
  ).toBe(true);
});
