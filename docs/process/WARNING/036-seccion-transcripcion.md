# 036: decisiones de la sección Transcripción y de la leyenda de hablantes (fase 2)

- **Contexto**: la fase 2 añade la sección y las moléculas de hablantes. Dos reglas del repo la limitan: `ui-structure` no admite etiquetas nativas fuera de `atoms/` y `shadcn/` (sin marcador de excepción), y el lint prohíbe que `features/` importe `UIBox`. No hay átomo de campo de texto ni de color.
- **Elegida**:
  - Las moléculas usan `Input` de `shadcn` para el nombre y el color (la misma vía que `UIField`); la carpeta `shadcn/` está exenta de la regla.
  - La leyenda usa `UIStack` con `role="list"` y `role="listitem"` en vez de `ul`/`li`, y `UIText` en vez de `span`.
  - Las features arman el layout con `UIStack`; el bloque de un hablante es un `UIStack` con su color de borde.
  - `transcription.title` es el encabezado de la sección (lo pide 02-diseno.md §5).
  - Dos claves nuevas, `transcription.job_failed` y `transcription.read_failed`, en vez de reutilizar `transcription.failed`, cuyo texto dice «No se pudo encolar».
  - `OPEN_SECTIONS` acepta `transcription` (la prueba de sincronía con el menú lo exige).
  - El inventario de moléculas (spec 008) incluye `UISpeakerCountField` y `UISpeakerLegend`.
  - La leyenda sincroniza el borrador ajustando el estado durante el render, sin efecto (la regla `set-state-in-effect` lo exige).
- **Descartadas**:
  - Un átomo nuevo `UIColorInput` o `UITextInput`: más superficie, más pruebas de inventario y ningún beneficio frente al `Input` de shadcn.
  - `UIBox` en las features: el lint lo prohíbe.
  - Reutilizar `transcription.failed` para trabajos fallidos: el texto miente sobre la causa.
- **Cómo revertir**: `git revert` del commit de la fase 2. Las claves nuevas se quitan de los tres catálogos.
- **Cómo comprobarla**: `python -m devtools test-runner --type=client-lint,client-typecheck,client-unit,ui-structure,i18n,budget` y, en `client/`, `bunx playwright test --config ../tests/e2e/playwright.config.ts` (las tres pruebas `transcription/`).
