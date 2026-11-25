# Spec 025, fase 2: Dependencias de Python al día

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `025-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-025/` o `tmp/spec-025/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Todas las dependencias directas en su última versión, con la cota igual al lock. **AC**: AC-4, AC-5. **Depende de**: fase 1.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C3: Cotas iguales al lock [AC-4, AC-5]

- **RED**: `tests/validators/test_python_version.py::test_ac4_bounds_match_lock`
  - WHEN `fastapi>=0.162.5` y el lock tiene otra versión THEN el test falla con el paquete y las dos versiones.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `uv lock --upgrade`, cotas nuevas en los dos `pyproject.toml` y las adaptaciones de API que pidan los tests. Verify: `uv run pytest -q` y `uv tree --outdated --depth 1` sin filas.
- **REFACTOR**: si la versión nueva de Starlette o httpx resuelve `PENDING/004-httpx-deprecado.md`, se borra la ficha y su fila.

## Matriz e2e

No aplica: esta fase no crea ni cambia un flujo del client.
