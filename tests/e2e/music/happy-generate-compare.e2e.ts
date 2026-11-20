import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToMusic, musicReplies, type MusicState } from '../support/music';

test('AC-8: dos estilos y dos variantes se encolan en un solo trabajo; Comparar muestra 4 pistas y «Elegir» deja una', async ({
  page,
}) => {
  const state: MusicState = { finished: true, chosen: null };
  const { calls } = await openApp(page, { replies: musicReplies(state) });
  await goToMusic(page);

  await page.getByRole('button', { name: 'Lofi relajado', exact: true }).click();
  await page.getByRole('button', { name: 'Corporativo minimalista', exact: true }).click();
  await page.getByRole('button', { name: 'Avanzado' }).click();
  await page.getByRole('spinbutton', { name: 'Variantes (1 a 6)' }).fill('2');
  await page.getByRole('button', { name: 'Generar' }).click();

  await expect
    .poll(() => calls.find((call) => call.method === 'POST' && call.path === '/jobs')?.body)
    .toEqual({
      kind: 'music',
      params: expect.objectContaining({ model: 'acestep', style: ['lofi-chill', 'corporate-minimal'], variants: 2 }),
    });
  await expect(page.locator('[data-track]')).toHaveCount(4);

  const chosen = page.locator('[data-track="acestep-lofi-chill-v2.wav"]');
  await chosen.getByRole('button', { name: 'Elegir' }).click();
  await expect
    .poll(() => calls.find((call) => call.method === 'POST' && call.path === '/jobs/9/choose')?.body)
    .toEqual({ file: 'acestep-lofi-chill-v2.wav' });
  await expect(chosen.getByRole('button', { name: 'Elegir' })).toHaveAttribute('aria-pressed', 'true');
});
