# 005: desvíos de diseño respecto de D-1, D-2, D-4 y D-8

- **Contexto**: la spec 005 fija las decisiones D-1 a D-10. Cuatro puntos se resolvieron de otra forma, y la revisión adversarial pidió que cada uno tenga su ficha, no solo su pendiente.
- **Elegida**:
  - **D-1 (shadcn)**: no se copió shadcn. Los elementos son nativos y la paleta (`CommandPalette`) es propia. Se copian componentes cuando una sección los use (decisión de T1).
  - **D-2 (CSP)**: `client/src-tauri/tauri.conf.json` amplía la CSP: `img-src 'self' data: blob:`, `media-src 'self' http://127.0.0.1:* blob:`, `style-src 'self' 'unsafe-inline'` y `font-src 'self' data:`. No se verificó cada directiva contra la app real; se amplió para no romper la reproducción ni los estilos.
  - **D-4 (tema y Geist)**: `public/theme-init.js` es un archivo externo, porque la CSP no admite scripts inline. Las fuentes son los woff2 de `public/fonts`; el paquete `geist` (1.9.2) queda declarado y no se importa.
  - **D-8 (restablecer)**: «Restablecer elecciones» confirma con `window.confirm`, no con `@tauri-apps/plugin-dialog`, que está en Cargo pero no en el paquete JS.
- **Descartadas**: apretar la CSP y añadir el plugin de diálogo dentro de la 005. Ambos cambios necesitan probarse en la app real y no bloquean las pruebas de la spec.
- **Cómo revertir**: restaurar la CSP de D-2 en `tauri.conf.json` y añadir `@tauri-apps/plugin-dialog` al paquete JS para el diálogo.
- **Cómo comprobarla**: `grep -n "csp" client/src-tauri/tauri.conf.json` y `grep -n "window.confirm" client/src/features/settings/SettingsPage.tsx`.
- **Pendiente**: lo que queda para después está en `docs/process/PENDING/005-desvios-d1-d8.md`.
- **Antes de**: el merge a `dev` no depende de estos puntos.
