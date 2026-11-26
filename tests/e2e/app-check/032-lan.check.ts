import { expect, setTheme, test } from './fixture';

// Ajustes > Integraciones > «Red local» (spec 032, AC-10) en la app real, en claro y en oscuro. Solo se mira: activarla
// pediría el UAC del firewall (03 §2, paso 1, con la app instalada).
for (const theme of ['light', 'dark'] as const) {
  test(`032 red local: the section in ${theme}`, async ({ app, shot, settled }) => {
    await setTheme(app, theme);
    await app.locator('a[href="#/settings"]').first().click();
    await expect(app.getByRole('main')).toBeVisible();
    await settled();
    const heading = app.getByRole('heading', { name: 'Red local' });
    await heading.scrollIntoViewIfNeeded();
    await expect(heading).toBeVisible();
    await expect(app.getByRole('switch', { name: 'Permitir que otros equipos de mi red usen Content Studio' })).not.toBeChecked();
    await expect(app.getByText('Se crea al activar la red local.')).toBeVisible();
    await expect(app.getByRole('button', { name: 'Emparejar dispositivo' })).toBeDisabled();
    await expect(app.getByText('No hay dispositivos emparejados.')).toBeVisible();
    await app.getByText('No hay dispositivos emparejados.').scrollIntoViewIfNeeded();
    await setTheme(app, theme);
    await shot(`032-lan-${theme}`);
  });
}
