import { expect, setTheme, test } from './fixture';

// Hablantes (spec 037, AC-1) en la app real, en claro y en oscuro, con su captura: el título de la sección y el formulario.
// El escenario no encola nada: la identificación real (pyannote en la GPU) va aparte, en docs/process/PENDING/.
for (const theme of ['light', 'dark'] as const) {
  test(`speakers: the section in ${theme}`, async ({ app, shot, settled }) => {
    await setTheme(app, theme);
    await app.getByRole('navigation').getByRole('link', { name: 'Hablantes', exact: true }).click();
    await expect(app.getByText('Identificar quién habla y cuándo', { exact: true })).toBeVisible();
    await expect(app.getByRole('textbox', { name: 'Archivo', exact: true })).toBeVisible();
    await settled();
    await setTheme(app, theme);
    await shot(`speakers-check-${theme}`);
  });
}
