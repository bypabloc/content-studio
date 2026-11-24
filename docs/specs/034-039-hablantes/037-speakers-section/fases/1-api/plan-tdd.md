# Spec 037, fase 1: API de diarización y proyecto del Editor

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `037-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-037/` o `tmp/spec-037/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: el resultado de una diarización por la API y un proyecto del Editor con un marcador por turno. **AC**: AC-4, AC-6. **Depende de**: nada.

## Ciclos TDD

#### Ciclo C1: resultado y archivos [AC-4]

- **RED**: `server/tests/unit/src/content_studio/api/routes/test_diarizations.py::test_ac4_resultado_y_archivos`
  - Con una carpeta falsa con los cuatro archivos y dos WAV: responde rutas, turnos y `split`. Sin WAV, `split: null`. Un trabajo `music` da 409.
- **GREEN**: `api/routes/diarizations.py` y su registro. Verify: `uv run pytest server/tests/unit/src/content_studio/api/routes/test_diarizations.py -q`.
- **REFACTOR**: ninguno.

#### Ciclo C2: proyecto del Editor [AC-6]

- **RED**: `server/tests/unit/src/content_studio/editor/test_from_diarization.py::test_ac6_clip_y_marcadores`
  - Un clip con la duración del original, marcadores solo para turnos de 0,5 s o más con el nombre del hablante, y un proyecto que pasa la validación del esquema del Editor.
- **GREEN**: `editor/from_diarization.py` y la ruta `POST /editor/projects/from-diarization`. Verify: `uv run pytest server/tests/unit/src/content_studio/editor -q`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: la UI está en la F2.
