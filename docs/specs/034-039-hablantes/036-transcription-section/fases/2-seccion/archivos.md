# Spec 036, fase 2: archivos

### Crear

- `client/src/features/transcription/TranscriptionPage.tsx`, `TranscriptionForm.tsx` y `TranscriptView.tsx`.
- `client/src/shared/components/molecules/UISpeakerCountField/index.tsx` y `UISpeakerLegend/index.tsx`.
- `client/src/shared/hooks/useSpeakers.ts`.
- Tests espejo en `client/tests/unit/src/...`.
- `tests/e2e/transcription/*.e2e.ts` y su API grabada en `tests/e2e/_api/transcription/`.
- `docs/process/01-done/transcription.md` — ficha nueva de la sección.
  - Verify: `bun run --cwd client test`

### Modificar

- `client/src/app/nav.ts` y `client/src/app/Shell.tsx`.
- El mapa de `UIIcon` — ícono `transcription` (de la librería de íconos que ya usa el proyecto).
- `server/src/content_studio/messages/{es,en,pt}.json` — textos de 02 §5.
  - Verify: `python -m devtools test-runner --type=client-lint,client-typecheck,client-unit,ui-structure,i18n,budget`

### Solo lectura

- `client/src/features/cleaner/CleanReview.tsx` y `shared/media/useSyncedMedia.ts` — palabras sincronizadas.
- `client/src/features/subtitles/SubtitlesPage.tsx` — patrón de encolado.
