import { expect, test } from '@playwright/test';
import { apiFixture, openApp, type Call } from '../support/app';

type Engine = {
  engine: string;
  family: string;
  size_gb: number;
  vram_gb: number;
  cpu: boolean;
  license: string;
  commercial: boolean;
  status: string;
  owner: string | null;
  size_bytes: number;
  job_id: number | null;
  verification: { ok: boolean } | null;
};

test('AC-8: instalar y verificar un motor desde Motores', async ({ page }) => {
  const engine = apiFixture<Engine[]>('engines/qwen-missing')[0]!;
  const engines = [engine];
  const calls: Call[] = [];
  await openApp(page, {
    settings: { 'welcome.done': true },
    replies: (call) => {
      calls.push(call);
      if (call.method === 'GET' && call.path === '/engines') return engines;
      if (call.method === 'GET' && call.path === '/system') return apiFixture('system/info');
      if (call.method === 'GET' && call.path === '/storage') return apiFixture('storage/paths');
      if (call.method === 'POST' && call.path === '/engines/qwen-0.6b/install') {
        engine.status = 'installed';
        engine.owner = 'app';
        return { id: 10, kind: 'engine.install', status: 'queued' };
      }
      if (call.method === 'POST' && call.path === '/engines/qwen-0.6b/verify') {
        engine.verification = { ok: true };
        return { id: 11, kind: 'engine.verify', status: 'queued' };
      }
      return undefined;
    },
  });
  await page.evaluate(() => { location.hash = '#/engines'; });
  const card = page.locator('[id="engine-card-qwen-0.6b"]');
  await card.getByRole('button', { name: 'Instalar', exact: true }).click();
  await expect.poll(() => calls.some((call) => call.method === 'POST' && call.path === '/engines/qwen-0.6b/install')).toBe(true);
  await card.getByRole('button', { name: 'Verificar', exact: true }).click();
  await expect.poll(() => calls.some((call) => call.method === 'POST' && call.path === '/engines/qwen-0.6b/verify')).toBe(true);
});
