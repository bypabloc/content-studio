# Spec 025, fase 1: Versión única y piso de los motores

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `025-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-025/` o `tmp/spec-025/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Una sola fuente de la versión y el piso calculado desde las recetas. **AC**: AC-1, AC-2, AC-3, AC-7. **Depende de**: nada.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C1: Versión única [AC-1, AC-2]

- **RED**: `tests/validators/test_python_version.py::test_ac2_versions_match`
  - WHEN `.python-version` dice 3.15 y `prepare.rs` dice 3.12 THEN el test falla nombrando el archivo que difiere; un segundo test (`test_ac1_venv_runs_pinned_version`) compara `sys.version_info` con el archivo.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `.python-version`, `requires-python = ">=3.15"`, matriz de `calidad.yml` con `python-version-file: .python-version`. Verify: `uv run pytest tests/validators/test_python_version.py -q`.
- **REFACTOR**: ninguno.

#### Ciclo C2: Piso desde las recetas [AC-3, AC-7]

- **RED**: `tests/validators/test_structure.py::test_ac3_floor_comes_from_recipes`
  - WHEN una receta de prueba declara 3.10 y otra 3.12 THEN el piso es (3, 10) y ruff/mypy de `pyproject.toml` deben decir lo mismo; hoy el valor está fijo en el test.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `engine_floor()` en `devtools/python_floor.py` (lee las recetas con `json`, stdlib); `test_structure.py` compila con `feature_version` de ese piso. Verify: `uv run pytest tests/validators -q`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: esta fase no crea ni cambia un flujo del client.
