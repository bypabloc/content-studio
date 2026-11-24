# Spec 038, fase 3: archivos

### Crear

- `client/src/features/editor/timeline/SubtitleLane.tsx` y su test.
- `tests/e2e/editor/happy-speaker-lanes.e2e.ts` y `tests/e2e/cleaner/happy-speakers.e2e.ts`, con su API grabada.

### Modificar

- `client/src/features/editor/Timeline.tsx` (o donde vive el carril) y `SubtitleTracksPanel.tsx`.
- `server/src/content_studio/clean/analyze_main.py`, `services/clean_analyze.py` y `api/routes/clean.py`.
- `client/src/features/cleaner/CleanerPage.tsx` y `CleanReview.tsx`.
- `server/src/content_studio/messages/{es,en,pt}.json`.
- `docs/process/01-done/editor.md` y `cleaner.md` — «Qué hace hoy» e Historial.
  - Verify: `python -m devtools test-runner --type=all`
