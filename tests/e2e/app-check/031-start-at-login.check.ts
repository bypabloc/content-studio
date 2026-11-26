import { execFile } from 'node:child_process';
import { chromium, expect, test } from '@playwright/test';

const CDP = process.env.APP_CHECK_CDP ?? '';

/** Ejecuta un comando sin shell y devuelve su salida (spec 031). */
function output(file: string, args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(file, args, (error, stdout) => (error ? reject(error) : resolve(stdout)));
  });
}

const RUN_KEY = 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run';

// Inicio con Windows (spec 031, AC-8): el interruptor escribe el valor Run de HKCU y, al desactivarlo, lo borra.
// El cierre de sesión (que el server arranque solo) se comprueba aparte, en la verificación.
test('031 AC-8: el interruptor escribe y borra el valor Run de HKCU', async () => {
  const browser = await chromium.connectOverCDP(CDP);
  const page = browser.contexts()[0].pages()[0];
  await page.evaluate(() => {
    window.location.hash = '#/settings';
  });
  const toggle = page.getByRole('checkbox', { name: 'Iniciar el servidor con Windows' });
  await toggle.scrollIntoViewIfNeeded();
  try {
    await toggle.click();
    await expect(toggle).toBeChecked();
    const value = await output('reg', ['query', RUN_KEY, '/v', 'ContentStudioServer']);
    expect(value).toContain('pythonw.exe" -m content_studio api up');
  } finally {
    if (await toggle.isChecked()) await toggle.click();
  }
  await expect(toggle).not.toBeChecked();
  await expect(output('reg', ['query', RUN_KEY, '/v', 'ContentStudioServer'])).rejects.toThrow();
  await browser.close();
});
