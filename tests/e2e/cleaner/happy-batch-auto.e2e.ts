import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { chooseFiles, cleanReplies, goToCleaner, newCleanState } from '../support/cleaner';

test('«Aplicar todos sin revisar» con tres archivos: cada uno sale listo con su render, sin pasar por la revisión', async ({
  page,
}) => {
  const state = newCleanState();
  const { calls } = await openApp(page, { replies: cleanReplies(state) });
  await goToCleaner(page);

  await chooseFiles(page, ['C:/fake/in/a.mp4', 'C:/fake/in/b.wav', 'C:/fake/in/c.mp4']);
  await page.getByRole('button', { name: 'Aplicar todos sin revisar' }).click();

  await expect
    .poll(
      () =>
        calls.filter(
          (call) =>
            call.method === 'POST' &&
            call.path === '/jobs' &&
            (call.body as { params?: { auto_render?: boolean } }).params?.auto_render === true,
        ).length,
    )
    .toBe(3);
  await expect(page.getByText('Listo', { exact: true })).toHaveCount(3);
  await expect(page.getByRole('button', { name: 'Revisar', exact: true })).toHaveCount(0);
});
