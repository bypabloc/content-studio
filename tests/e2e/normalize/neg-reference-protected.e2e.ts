import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { chooseFiles, goToSection, mediaBodies, mediaReplies, newMediaState } from '../support/media';

test('Normalizar: un archivo de referencia de voz no se normaliza y el aviso dice por qué', async ({ page }) => {
  const state = newMediaState();
  const { calls } = await openApp(page, {
    replies: mediaReplies(state, () => ({
      status: 422,
      body: {
        code: 'reference_protected',
        params: {},
        message: 'Este archivo es una referencia de voz: no se normaliza.',
      },
    })),
  });
  await goToSection(page, 'Normalizar');

  await chooseFiles(page, ['C:/fake/server/data/narration/reference/jhosse/a.wav']);
  await page.getByRole('button', { name: 'Normalizar', exact: true }).click();

  await expect(page.getByText('Este archivo es una referencia de voz: no se normaliza.')).toBeVisible();
  expect(mediaBodies(calls)).toHaveLength(1);
  expect(state.jobs).toHaveLength(0);
});
