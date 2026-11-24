# Spec 036, fase 2: sección Transcripción

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `036-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-036/` o `tmp/spec-036/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: la sección completa con los componentes compartidos de hablantes. **AC**: AC-1 a AC-7. **Depende de**: F1.

## Ciclos TDD

#### Ciclo C3: componentes de hablantes [AC-2, AC-5]

- **RED**: `client/tests/unit/src/shared/components/molecules/UISpeakerCountField.test.tsx` (los tres modos y lo que devuelve) y `UISpeakerLegend.test.tsx` (renombrar, cambiar el color y `onChange`; nombre accesible del selector de color).
- **GREEN**: las dos moléculas y `shared/hooks/useSpeakers.ts`. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

#### Ciclo C4: navegación y formulario [AC-1, AC-2, AC-3]

- **RED**: `client/tests/unit/src/app/nav.test.ts` (la entrada nueva) y `features/transcription/TranscriptionForm.test.tsx` (el cuerpo exacto del `POST /jobs`, y el interruptor deshabilitado si `GET /engines` no trae `pyannote` instalado).
- **GREEN**: `nav.ts`, `Shell.tsx`, `TranscriptionPage.tsx` y `TranscriptionForm.tsx`. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

#### Ciclo C5: resultado [AC-4, AC-6, AC-7]

- **RED**: `features/transcription/TranscriptView.test.tsx`:
  - con y sin hablantes;
  - clic en una palabra mueve `currentTime`;
  - «Exportar texto» llama a la ruta;
  - «Crear subtítulos» llama a `from-transcript` y navega.
- **GREEN**: `TranscriptView.tsx`. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

## Matriz e2e

| Archivo | Recorre | AC |
| :--- | :--- | :--- |
| `tests/e2e/transcription/happy-transcribe-speakers.e2e.ts` | Open Transcription, pick file, enable speakers, exact 2, start; job finishes; blocks show two names; rename to Ana; export text; create subtitles navigates | AC-1, AC-2, AC-4, AC-5, AC-6, AC-7 |
| `tests/e2e/transcription/happy-transcribe-plain.e2e.ts` | Transcribe without speakers; paragraphs per segment | AC-4 |
| `tests/e2e/transcription/neg-no-diarization-engine.e2e.ts` | Engine missing: switch disabled with link to Engines | AC-3 |
