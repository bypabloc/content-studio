# Spec 034, fase 3: archivos

## client/src/features/

### Crear

- `client/src/features/engines/HfTokenField.tsx` — campo, estado guardado y enlace.
- `client/tests/unit/src/features/engines/HfTokenField.test.tsx`.
- `tests/e2e/engines/happy-hf-token.e2e.ts`, `tests/e2e/engines/neg-gated-install.e2e.ts` y su API grabada en `tests/e2e/_api/engines/`.
  - Verify: `bun run --cwd client test`

### Modificar

- `client/src/features/engines/EnginesPage.tsx` — grupo `diarization`.
- `client/src/features/engines/EngineCard.tsx` — monta `HfTokenField` y deshabilita «Instalar».
- El componente de «Acerca de» en `client/src/features/settings/` — la atribución.
- `server/src/content_studio/messages/{es,en,pt}.json` — textos de 02 §5.
- `docs/process/01-done/engines.md` — «Qué hace hoy» (motores restringidos con token) e Historial.
  - Verify: `python -m devtools test-runner --type=client-lint,client-typecheck,client-unit,ui-structure,i18n`
