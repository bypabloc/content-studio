import { expect, test } from '@playwright/test';
import { API, openApp } from '../support/app';
import { goToMusic, musicReplies, type MusicState } from '../support/music';

test('AC-8: si el server se durmió, Generar reconecta y el trabajo se encola', async ({ page }) => {
  const state: MusicState = { finished: true, chosen: null };
  const { calls } = await openApp(page, { replies: musicReplies(state) });
  await goToMusic(page);

  // El server se durmió: la primera llamada a /jobs no llega. La app pide la conexión otra vez y la repite una vez.
  let dropped = false;
  await page.route(`${API}/jobs`, (route) => {
    if (route.request().method() === 'POST' && !dropped) {
      dropped = true;
      return route.abort('connectionrefused');
    }
    return route.fallback();
  });

  await page.getByRole('button', { name: 'Lofi relajado', exact: true }).click();
  await page.getByRole('button', { name: 'Generar' }).click();

  await expect.poll(() => calls.some((call) => call.method === 'POST' && call.path === '/jobs')).toBe(true);
  const commands = await page.evaluate(() => (window as unknown as { __commands: string[] }).__commands);
  expect(commands.filter((command) => command === 'get_connection')).toHaveLength(2);
});
