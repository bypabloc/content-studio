import { expect, setTheme, test } from './fixture';

// Cada sección de la barra lateral (navItems en client/src/app/nav.ts), en claro y en oscuro, con su captura.
for (const theme of ['light', 'dark'] as const) {
  test(`smoke: every section in ${theme}`, async ({ app, shot }) => {
    await setTheme(app, theme);
    const targets = await app
      .getByRole('navigation')
      .getByRole('link')
      .evaluateAll((links) => links.map((link) => link.getAttribute('href') ?? '').filter((href) => href.startsWith('#/')));
    expect(targets.length).toBeGreaterThan(0);
    for (const href of targets) {
      const id = href.slice(2);
      await app.locator(`a[href="${href}"]`).first().click();
      await expect(app.locator(`a[href="${href}"][aria-current="page"]`).first()).toBeVisible();
      await expect(app.getByRole('main')).toBeVisible();
      await shot(`${id}-${theme}`);
    }
  });
}
