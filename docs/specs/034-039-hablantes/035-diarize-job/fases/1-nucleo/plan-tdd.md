# Spec 035, fase 1: unión, bloques y exportaciones

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `035-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-035/` o `tmp/spec-035/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: las funciones puras que todo lo demás usa. **AC**: AC-1, AC-2, AC-3. **Depende de**: nada.

## Ciclos TDD

#### Ciclo C1: palabra a hablante y bloques [AC-1, AC-2]

- **RED**:
  - `server/tests/unit/src/content_studio/diarization/test_assign.py::test_ac1_overlap_gap_and_far_words`: tabla con un solape parcial entre dos turnos, una palabra en un hueco de 0,4 s, otra a 1,5 s de todo, otra sin `end` y una lista de turnos vacía.
  - `test_blocks.py::test_ac2_corta_y_absorbe`.
  - Doctest de `segment_speaker`.
- **GREEN**: `diarization/assign.py` y `diarization/blocks.py`. Verify: `uv run pytest server/tests/unit/src/content_studio/diarization -q`.
- **REFACTOR**: comparar con un test de caracterización contra la búsqueda completa (sin ventana) en 200 palabras aleatorias con semilla fija.

#### Ciclo C2: exportaciones y nombres [AC-3]

- **RED**: `test_exports.py::test_ac3_rttm_csv_json` con las líneas exactas esperadas, más `test_speakers.py::test_paleta_y_nombres` (colores por orden y repetición después del octavo).
- **GREEN**: `diarization/exports.py` y `diarization/speakers.py`. Verify: `uv run pytest server/tests/unit/src/content_studio/diarization -q`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica.
