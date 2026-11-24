# Spec 037, fase 2: archivos

### Crear

- `client/src/features/speakers/SpeakersPage.tsx`, `SpeakersForm.tsx`, `SpeakerTimeline.tsx` y `SpeakerFiles.tsx`.
- Tests espejo y `tests/e2e/speakers/*.e2e.ts`, con su API grabada en `tests/e2e/_api/speakers/`.
- `tests/e2e/app-check/speakers.check.ts` — recorre la sección con un trabajo real.
  - Verify: `bun run --cwd client test`

### Modificar

- `client/src/app/nav.ts`, `Shell.tsx` y el mapa de `UIIcon` (ícono `speakers`).
- `server/src/content_studio/messages/{es,en,pt}.json` — textos de 02 §5.
- `docs/process/01-done/diarization.md` — la sección Hablantes en «Qué hace hoy» y en el Historial.
  - Verify: `python -m devtools test-runner --type=client-lint,client-typecheck,client-unit,ui-structure,i18n,budget`

### Solo lectura

- `client/src/features/cleaner/ReviewWave.tsx` — WaveSurfer y regiones.
- `client/src/shared/navigation/` — «Abrir en Editor».
