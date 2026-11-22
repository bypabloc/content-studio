import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { chooseFiles, cleanReplies, goToCleaner, newCleanState } from '../support/cleaner';

test('un archivo que el limpiador no acepta: el server lo rechaza, el motivo se muestra y el lote no cambia', async ({
  page,
}) => {
  const state = newCleanState();
  const reject = {
    status: 422,
    body: {
      code: 'clean.unsupported_format',
      params: { path: 'C:/fake/in/notas.txt' },
      message: 'C:/fake/in/notas.txt no es un formato de audio o video que acepte el limpiador.',
    },
  };
  const { calls } = await openApp(page, { replies: cleanReplies(state, reject) });
  await goToCleaner(page);

  await chooseFiles(page, ['C:/fake/in/notas.txt']);
  await page.getByRole('button', { name: 'Analizar', exact: true }).click();

  await expect
    .poll(() => calls.some((call) => call.method === 'POST' && call.path === '/jobs'))
    .toBe(true);
  await expect(page.getByRole('alert').filter({ hasText: 'no es un formato de audio o video' })).toBeVisible();
  await expect(page.getByText('Todavía no hay análisis.')).toBeVisible();
  expect(state.analyses).toHaveLength(0);
});
