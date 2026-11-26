import { expect, setTheme, test } from './fixture';

// Transcripción (spec 036, AC-1) en la app real, en claro y en oscuro, con su captura: el título de la sección y el
// formulario. El escenario no encola nada: la corrida real con hablantes va aparte.
for (const theme of ['light', 'dark'] as const) {
  test(`transcription: the section in ${theme}`, async ({ app, shot, settled }) => {
    await setTheme(app, theme);
    await app.getByRole('navigation').getByRole('link', { name: 'Transcripción' }).click();
    await expect(app.getByRole('main').getByRole('heading', { name: 'Transcribir un archivo', level: 2 })).toBeVisible();
    await expect(app.getByRole('textbox', { name: 'Archivo' })).toBeVisible();
    await settled();
    await setTheme(app, theme);
    await shot(`transcription-check-${theme}`);
  });
}
