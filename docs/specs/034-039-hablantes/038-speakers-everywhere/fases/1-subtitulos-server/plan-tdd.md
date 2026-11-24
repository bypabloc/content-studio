# Spec 038, fase 1: Subtítulos (server)

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `038-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-038/` o `tmp/spec-038/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: documentos de subtítulos con hablantes, desde cualquier origen, con color y prefijo. **AC**: AC-1, AC-2, AC-3, AC-4. **Depende de**: nada.

## Ciclos TDD

#### Ciclo C1: segmentación y documento [AC-1, AC-2]

- **RED**:
  - `server/tests/unit/src/content_studio/subtitles/test_segment.py::test_ac1_corta_en_cambio_de_hablante`.
  - `test_document.py::test_ac2_split_merge_set_speaker`.
  - `server/tests/integration/test_characterization.py::test_ac1_sin_hablantes_igual`.
- **GREEN**: `segment.py` y `document.py`. Verify: `uv run pytest server/tests/unit/src/content_studio/subtitles -q`.
- **REFACTOR**: ninguno.

#### Ciclo C2: orígenes con hablantes [AC-2]

- **RED**: `test_create_main.py::test_ac2_diarize_y_origenes` (con `diarize_file` y la transcripción simulados) y `api/routes/test_subtitles.py::test_ac2_from_transcript_con_hablantes`, que también cubre el origen `cleaner` con `remap`.
- **GREEN**: `sources.py`, `create_main.py`, `services/subtitles_create.py` (validación de los parámetros nuevos) y `api/routes/subtitles.py`. Verify: `uv run pytest server/tests/unit/src/content_studio -q -k subtitles`.
- **REFACTOR**: ninguno.

#### Ciclo C3: ASS y exportación [AC-3, AC-4]

- **RED**: `test_ass.py::test_ac3_color_por_hablante` (eventos de `classic` y `social` con `\1c`; karaoke sin cambio; doctest del color) y `test_formats.py::test_ac4_prefijo_srt_vtt`.
- **GREEN**: `ass.py`, `formats.py`, `export.py` y la ruta `export`. Verify: `uv run pytest server/tests/unit/src/content_studio/subtitles -q`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: la UI está en la F2.
