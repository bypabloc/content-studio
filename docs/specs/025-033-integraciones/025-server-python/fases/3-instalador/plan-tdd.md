# Spec 025, fase 3: Instalador con la Python nueva

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `025-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-025/` o `tmp/spec-025/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: La app instalada prepara la versión de `.python-version` y recrea el venv si cambió. **AC**: AC-6. **Depende de**: fase 1.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C4: Recrear el venv al cambiar la Python [AC-6]

- **RED**: `client/src-tauri/src/bootstrap/prepare.rs::tests::recreates_venv_when_python_changes`
  - Given un layout con un venv marcado 3.12 When `prepare` corre con `PYTHON` 3.15 Then el runner recibe `uv python install 3.15` y `uv sync` con `--python 3.15` tras borrar el venv del server; hoy lo salta.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `PYTHON` generado en `build.rs` desde `.python-version` (o comprobado por C1) y la marca de versión en el venv. Verify: `python -m devtools test-runner --type=tauri-check`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: esta fase no crea ni cambia un flujo del client.
