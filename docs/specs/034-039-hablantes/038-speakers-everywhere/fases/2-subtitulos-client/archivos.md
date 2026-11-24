# Spec 038, fase 2: archivos

### Modificar

- `client/src/features/subtitles/cues.ts`, `CueList.tsx`, `SubtitlesEditor.tsx`, `ass.ts` y `SubtitlesPage.tsx`.
- Tests espejo; `tests/e2e/subtitles/happy-speakers.e2e.ts` y `neg-speakers-no-engine.e2e.ts`, con su API grabada.
- `server/src/content_studio/messages/{es,en,pt}.json` — textos de Subtítulos.
- `docs/process/01-done/subtitles.md` — «Qué hace hoy» e Historial.
  - Verify: `python -m devtools test-runner --type=client-lint,client-typecheck,client-unit,ui-structure,i18n`
