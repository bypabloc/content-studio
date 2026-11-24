# Spec 038, fase 2: Subtítulos (client)

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `038-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-038/` o `tmp/spec-038/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: crear subtítulos con hablantes y editarlos. **AC**: AC-3, AC-5, AC-6. **Depende de**: F1.

## Ciclos TDD

#### Ciclo C4: chip, leyenda, vista previa y exportar [AC-3, AC-5]

- **RED**:
  - `client/tests/unit/src/features/subtitles/cues.test.ts`: `setCueSpeaker`, y que `split` y `merge` conservan el hablante.
  - `CueList.test.tsx`: el chip y el menú.
  - `ass.test.ts`: el mismo `\1c` que el server, con una fixture compartida.
  - `SubtitlesEditor.test.tsx`: la leyenda y «Incluir nombres».
- **GREEN**: `cues.ts`, `CueList.tsx`, `SubtitlesEditor.tsx` y `ass.ts`. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

#### Ciclo C5: crear con hablantes [AC-6]

- **RED**: `SubtitlesPage.test.tsx`: el cuerpo de `POST /jobs` con `model`, `language` y `diarize`; el interruptor deshabilitado si falta el motor.
- **GREEN**: `SubtitlesPage.tsx`. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

## Matriz e2e

| Archivo | Recorre | AC |
| :--- | :--- | :--- |
| `tests/e2e/subtitles/happy-speakers.e2e.ts` | New project from file with speakers; cues show chips; change a cue speaker; rename in legend; export SRT with names | AC-5, AC-6, AC-4 |
| `tests/e2e/subtitles/neg-speakers-no-engine.e2e.ts` | Engine missing: switch disabled with link | AC-6 |
