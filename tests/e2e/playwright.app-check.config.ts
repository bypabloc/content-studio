import { defineConfig } from '@playwright/test';

// `python -m devtools app-check run` (spec 024): la ventana real de Tauri por CDP, sin webServer ni navegador propio.
// Una sola ventana: los escenarios corren de a uno. Sus resultados van a la carpeta de la corrida.
const RUN = process.env.APP_CHECK_RUN ?? '../../tmp/app-check/manual';

export default defineConfig({
  testDir: './app-check',
  testMatch: '**/*.check.ts',
  outputDir: `${RUN}/results`,
  reporter: [['list']],
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 180_000,
});
