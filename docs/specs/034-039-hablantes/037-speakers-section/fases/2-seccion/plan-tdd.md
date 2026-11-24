# Spec 037, fase 2: sección Hablantes

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `037-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-037/` o `tmp/spec-037/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: la sección completa. **AC**: AC-1 a AC-7. **Depende de**: F1.

## Ciclos TDD

#### Ciclo C3: navegación, formulario y `from_job` [AC-1, AC-7]

- **RED**: `client/tests/unit/src/features/speakers/SpeakersForm.test.tsx` (el cuerpo de `POST /jobs`) y `SpeakersPage.test.tsx::from_job` (carga el resultado sin encolar).
- **GREEN**: `nav.ts`, `Shell.tsx`, `SpeakersPage.tsx` y `SpeakersForm.tsx`. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

#### Ciclo C4: línea de tiempo [AC-2, AC-3]

- **RED**: `client/tests/unit/src/features/speakers/SpeakerTimeline.test.tsx` (WaveSurfer simulado):
  - una región por turno, con su color y su etiqueta;
  - clic en una región, reproducir;
  - `focusSpeaker` atenúa las demás;
  - ← y → saltan entre turnos;
  - un nombre nuevo cambia la etiqueta.
- **GREEN**: `SpeakerTimeline.tsx` con `UISpeakerLegend`. Verify: `bun run --cwd client test`.
- **REFACTOR**: si al implementar se ve que `ReviewWave` y `SpeakerTimeline` comparten la carga de WaveSurfer, se extrae a `shared/media/useWaveSurfer.ts` y se registra en `WARNING`.

#### Ciclo C5: archivos, audio por hablante y Editor [AC-4, AC-5, AC-6]

- **RED**: `client/tests/unit/src/features/speakers/SpeakerFiles.test.tsx`:
  - lista de archivos y «Abrir carpeta»;
  - «Un audio por hablante» encola `diarize.split` y, cuando `split` llega, muestra un reproductor por hablante;
  - «Abrir en el Editor» llama a la ruta y navega.
- **GREEN**: `SpeakerFiles.tsx`. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

## Matriz e2e

| Archivo | Recorre | AC |
| :--- | :--- | :--- |
| `tests/e2e/speakers/happy-diarize-timeline.e2e.ts` | Open Speakers, pick file, auto, identify; timeline regions with two names; rename; focus one speaker and jump with arrows | AC-1, AC-2, AC-3 |
| `tests/e2e/speakers/happy-split-and-editor.e2e.ts` | Files listed; split audio shows two players; open in Editor navigates with markers | AC-4, AC-5, AC-6 |
| `tests/e2e/speakers/happy-from-job.e2e.ts` | Open from queue with from_job; result shown without a new job | AC-7 |
