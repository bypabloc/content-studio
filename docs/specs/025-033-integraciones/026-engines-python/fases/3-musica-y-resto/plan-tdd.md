# Spec 026, fase 3: Música, whisper, visión y asistente

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `026-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-026/` o `tmp/spec-026/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Las siete recetas restantes al día. **AC**: AC-1, AC-2, AC-4, AC-6. **Depende de**: fase 1.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C4: Recetas restantes [AC-1, AC-2, AC-4, AC-6]

- **RED**: `server/tests/integration/test_venvs.py (-m local, con la carpeta aislada)`
  - WHEN `acestep`, `heartmula`, `faster-whisper`, `vision`, `llama-cpp`, `gemma-4-e4b` y `qwen3.5-9b` se instalan en la carpeta aislada THEN cada venv importa su librería; antes de subir, el test con las versiones nuevas en `LIBRARIES` falla.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: misma rutina que C3; `llama-cpp` sube al último build CUDA de Windows con su sha256. Verify: `uv run pytest -m local`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: esta fase no crea ni cambia un flujo del client.
