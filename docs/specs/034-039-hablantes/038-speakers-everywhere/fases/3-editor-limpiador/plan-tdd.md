# Spec 038, fase 3: Editor y Limpiador

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `038-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-038/` o `tmp/spec-038/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: el hablante en la pista de subtítulos del Editor y en la revisión del Limpiador. **AC**: AC-7, AC-8. **Depende de**: F2.

## Ciclos TDD

#### Ciclo C6: Editor [AC-7]

- **RED**: `client/tests/unit/src/features/editor/timeline/SubtitleLane.test.tsx` (un bloque por cue, posición y ancho según la escala, color, nombre y neutro sin hablante) y `SubtitleTracksPanel.test.tsx` (`diarize: true` en el trabajo `transcribe`).
- **GREEN**: `SubtitleLane.tsx`, `Timeline.tsx` (monta el carril en las pistas de subtítulos) y `SubtitleTracksPanel.tsx`. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

#### Ciclo C7: Limpiador [AC-8]

- **RED**:
  - `server/tests/unit/src/content_studio/clean/test_analyze_main.py::test_ac8_diarize`: `cuts.json` con `diarization` y `diarize_file` simulado.
  - `api/routes/test_clean.py::test_ac8_revision_con_hablantes`.
  - `client/tests/unit/src/features/cleaner/CleanReview.test.tsx`: el color por palabra y la leyenda.
  - `CleanerPage.test.tsx`: el interruptor.
- **GREEN**: `clean/analyze_main.py`, `services/clean_analyze.py`, `api/routes/clean.py`, `CleanerPage.tsx` y `CleanReview.tsx`. Verify: `uv run pytest -q && bun run --cwd client test`.
- **REFACTOR**: ninguno.

## Matriz e2e

| Archivo | Recorre | AC |
| :--- | :--- | :--- |
| `tests/e2e/editor/happy-speaker-lanes.e2e.ts` | Transcribe mix with speakers; subtitle lane shows colored cue blocks with names | AC-7 |
| `tests/e2e/cleaner/happy-speakers.e2e.ts` | Analyze with speakers; review words colored, legend visible; subtitle from cleaner keeps speakers | AC-8 |
