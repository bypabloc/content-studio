# 013: presupuesto de JS inicial del client, de 232 a 233 kB gzip

- **Contexto**: `client/budget.json` fija 232 kB gzip para el JS de arranque. Con la sección Limpiador, el arranque mide 232,54 kB y la etapa `budget` falla.
- **Elegida**: subir el presupuesto a 233 kB. Lo que crece en el arranque son las claves nuevas de `es` (`shared/i18n/catalogs.ts` importa solo ese catálogo, que tiene todas las claves y sirve de respaldo). La sección Limpiador, sus plugins de onda y el selector de whisper van en chunks perezosos (`lazy` en `Shell.tsx`), así que no suman al arranque.
- **Descartadas**:
  - Bajar código de otra parte para compensar: mezcla dos cambios sin relación en un mismo commit.
  - Partir el catálogo `es` por sección: es un cambio de `i18n` que esta spec no necesita; si el presupuesto vuelve a apretar, sale de aquí.
- **Cómo revertir**: bajar `initialJsGzipKb` a 232 cuando se parta el catálogo `es` o se reduzcan sus claves.
- **Cómo comprobarla**: `python -m devtools test-runner --type=budget` (mide el bundle de `vite build`).
