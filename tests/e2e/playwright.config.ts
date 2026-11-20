import { defineConfig, devices } from '@playwright/test';

const PORT = 4173;

// La app construida (client/dist) servida por vite preview. La API va simulada en cada test (support/app.ts).
export default defineConfig({
  testDir: '.',
  testMatch: '**/*.e2e.ts',
  outputDir: '../../tmp/e2e/results',
  reporter: [['list']],
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  // Las pruebas esperan la UI en español: con el idioma del navegador en inglés, «Sistema» abriría en inglés (spec 007).
  use: { baseURL: `http://127.0.0.1:${PORT}`, locale: 'es-419' },
  projects: [
    {
      name: 'desktop-chromium',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } },
    },
  ],
  webServer: {
    command: `bun run --cwd ../../client build && bun run --cwd ../../client preview -- --port ${PORT} --strictPort`,
    url: `http://127.0.0.1:${PORT}`,
    // Sin reutilizar: un servidor ajeno en el puerto probaría otro build, no el de este worktree.
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
