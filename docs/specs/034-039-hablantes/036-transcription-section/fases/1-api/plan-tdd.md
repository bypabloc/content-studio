# Spec 036, fase 1: API de transcripción y hablantes

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `036-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-036/` o `tmp/spec-036/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: leer la transcripción de un trabajo, editar sus hablantes y exportar el texto. **AC**: AC-5, AC-6. **Depende de**: nada.

## Ciclos TDD

#### Ciclo C1: transcripción y hablantes [AC-5]

- **RED**: `server/tests/unit/src/content_studio/api/routes/test_speakers.py::test_ac5_get_put_valida`
  - Con un trabajo `transcribe` falso en `tmp_path`: `GET transcript` une los dos archivos, `PUT` guarda y responde con lo guardado, un nombre de 41 caracteres o un color `red` dan 422, un id desconocido da 422, y si existe `turns.csv` lo regenera.
- **GREEN**: `api/routes/speakers.py` y su registro. Verify: `uv run pytest server/tests/unit/src/content_studio/api/routes/test_speakers.py -q`.
- **REFACTOR**: ninguno.

#### Ciclo C2: TXT por turnos [AC-6]

- **RED**: `server/tests/unit/src/content_studio/diarization/test_transcript_text.py::test_ac6_txt_por_turnos`: el texto exacto con y sin marcas, y sin hablantes. Más `test_speakers.py::test_ac6_export_escribe_archivo`.
- **GREEN**: `diarization/transcript_text.py` y la ruta `export`. Verify: `uv run pytest server/tests/unit/src/content_studio -q -k "transcript or speakers"`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: la UI está en la F2.
