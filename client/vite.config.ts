import { fileURLToPath, URL } from 'node:url';
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@messages': fileURLToPath(new URL('../server/src/content_studio/messages', import.meta.url)),
    },
  },
  server: { port: 1420, strictPort: true, fs: { allow: [fileURLToPath(new URL('..', import.meta.url))] } },
  test: {
    environment: 'jsdom',
    // Con un worker por núcleo, jsdom y los `lazy()` de los selectores pasan del margen de espera en equipos cargados:
    // con 6 workers, molecules y features pasan completos; con 23, falla un test. Ver WARNING 008-workers-vitest.
    maxWorkers: 6,
    setupFiles: ['tests/unit/setup.ts'],
    include: ['tests/unit/src/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      include: ['src/**'],
      // shadcn es código de proveedor copiado (spec 008, D-1): se prueba con el smoke test, no archivo por archivo.
      exclude: ['src/components/ui/**', 'src/shared/components/shadcn/**', 'src/main.tsx', 'src/**/*.d.ts'],
      thresholds: { perFile: true, lines: 80, functions: 80, branches: 80, statements: 80 },
    },
  },
});
