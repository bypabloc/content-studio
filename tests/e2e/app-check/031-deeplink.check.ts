import { execFile } from 'node:child_process';
import { chromium, expect, test } from '@playwright/test';

const CDP = process.env.APP_CHECK_CDP ?? '';

/** Ejecuta un comando sin shell y devuelve su salida (spec 031). */
function output(file: string, args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(file, args, (error, stdout) => (error ? reject(error) : resolve(stdout)));
  });
}

// Un enlace con la app abierta (spec 031, AC-1 y AC-5): Windows lo manda a la instancia abierta, que cambia de sección.
// La ventana escucha los enlaces al montarse: se vuelve a intentar hasta que la sección cambia.
test('031 AC-1/AC-5: un enlace abre la sección en la ventana ya abierta', async () => {
  const browser = await chromium.connectOverCDP(CDP);
  const page = browser.contexts()[0].pages()[0];
  await expect(page.getByRole('navigation', { name: 'Secciones' })).toBeVisible({ timeout: 90_000 });
  await expect(async () => {
    await output('cmd', ['/c', 'start', '', 'content-studio://open/music']);
    await expect(page).toHaveURL(/#\/music$/, { timeout: 3_000 });
  }).toPass({ timeout: 60_000, intervals: [1_000] });
  await browser.close();
});
