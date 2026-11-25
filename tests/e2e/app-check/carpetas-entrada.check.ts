import { expect, setTheme, test } from './fixture';

// Ajustes > Integraciones > «Carpetas de entrada» (spec 030, AC-9), en claro y en oscuro, con su captura. La sección
// queda debajo de Integraciones: la captura baja hasta su título para que se vea el formulario entero.
for (const theme of ['light', 'dark'] as const) {
  test(`carpetas de entrada: the section in ${theme}`, async ({ app, shot, settled }) => {
    await setTheme(app, theme);
    await app.locator('a[href="#/settings"]').first().click();
    await expect(app.getByRole('main')).toBeVisible();
    await settled();
    const heading = app.getByRole('heading', { name: 'Carpetas de entrada' });
    await heading.scrollIntoViewIfNeeded();
    await expect(heading).toBeVisible();
    await expect(app.getByRole('button', { name: 'Elegir carpeta' })).toBeVisible();
    await expect(app.getByRole('button', { name: 'Agregar carpeta' })).toBeDisabled();
    await setTheme(app, theme);
    await shot(`carpetas-entrada-${theme}`);
  });
}
