import { expect, test } from '@playwright/test';
import { API, openApp } from '../support/app';
import { readOnlyApi } from '../app-check/support/readonly';

test('spec 024 AC-9: en solo lectura, las escrituras a la API se abortan y se anotan; las lecturas pasan', async ({ page }) => {
  const { calls } = await openApp(page);
  const blocked = await readOnlyApi(page, new RegExp(`^${API.replace(/[.]/g, '\\.')}/`));
  const result = await page.evaluate(async (api) => {
    const write = await fetch(`${api}/settings/ui.theme`, { method: 'PUT', body: '{"value":"dark"}' }).then(
      () => 'sent',
      () => 'aborted',
    );
    const read = await fetch(`${api}/jobs`).then((response) => response.status);
    return { write, read };
  }, API);
  expect(result).toEqual({ write: 'aborted', read: 200 });
  expect(blocked).toEqual(['PUT /settings/ui.theme']);
  expect(calls.some((call) => call.method === 'PUT' && call.path === '/settings/ui.theme')).toBe(false);
});
