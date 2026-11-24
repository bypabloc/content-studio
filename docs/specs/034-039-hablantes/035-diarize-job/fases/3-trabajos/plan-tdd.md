# Spec 035, fase 3: trabajos, caché y CLI

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `035-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-035/` o `tmp/spec-035/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: los trabajos `diarize`, `diarize.split` y `transcribe` con hablantes por la cola, la caché y `studio diarize`. **AC**: AC-7, AC-8, AC-9, AC-10, AC-11. **Depende de**: F2.

## Ciclos TDD

#### Ciclo C6: servicio `diarize`, caché y atajos [AC-7, AC-8]

- **RED**:
  - `server/tests/unit/src/content_studio/services/test_diarize.py::test_ac7_validacion_y_comando`: los errores de AC-7 y el comando.
  - `test_diarize_split.py`.
  - `diarization/test_cache.py::test_ac8_reusa_sin_modelo` y `test_run.py::test_ac8_atajos_sin_modelo`: con `subprocess` simulado, la segunda llamada no lanza `diarize_main`; con 2 s o `num_speakers=1`, tampoco.
- **GREEN**: migración, `diarization/cache.py`, `run.py` y `job_main.py`, `services/diarize.py`, `services/diarize_split.py` y `services/registry.py`. Verify: `uv run pytest server/tests/unit/src/content_studio/services server/tests/unit/src/content_studio/diarization -q`.
- **REFACTOR**: ninguno.

#### Ciclo C7: `transcribe` con hablantes [AC-9, AC-10]

- **RED**:
  - `diarization/test_transcribe_speakers_main.py::test_ac9_palabras_con_hablante`: con los dos subprocesos simulados, `words.json` trae `speaker` en palabras y segmentos, y el progreso emite los dos tramos.
  - `server/tests/integration/test_characterization.py::test_ac10_transcribe_sin_diarize_igual`: el comando y `words_payload` sin cambios.
- **GREEN**: `diarization/transcribe_speakers_main.py` y `services/transcribe.py`. Verify: `uv run pytest -q`.
- **REFACTOR**: ninguno.

#### Ciclo C8: `studio diarize` [AC-11]

- **RED**: `server/tests/unit/src/content_studio/cli/test_diarize.py::test_ac11_parser_y_error` (parser, encolado simulado y exit 2).
- **GREEN**: `cli/diarize.py` y la línea en `cli/main.build_parser`. Verify: `uv run pytest server/tests/unit/src/content_studio/cli -q`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: no hay UI en esta spec.
