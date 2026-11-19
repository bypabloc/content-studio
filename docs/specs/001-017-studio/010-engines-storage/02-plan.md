# 010: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo, con cobertura ≥ 80 % por archivo. Ningún test unitario descarga nada: los pasos se prueban con comandos `python -c`.

## 1. Ciclos TDD

#### Ciclo 1: rutas dinámicas [AC-1]

- **RED**: `test_paths.py`, con los tres modos (setting, dev e installed).
- **GREEN**: las funciones de `paths.py` y el reemplazo de las constantes en todos sus usos.
- **REFACTOR**: `graphify affected "paths" --depth 2` sin usos de las constantes viejas.

#### Ciclo 2: reubicación en el server [AC-7]

- **RED**: `storage/test_relocate.py` (mismo volumen, copia verificada, interrupción y reescritura de `.pth`).
- **GREEN**: `git mv` de la lógica de `devtools/move_data.py` a `content_studio/storage/relocate.py`, que devtools pasa a importar. `services/storage_move.py` y su ruta en la API.
- **REFACTOR**: ninguno.

#### Ciclo 3: herramientas del sistema [AC-6]

- **RED**: `system/test_tools.py`, con `which`, `subprocess` y el registro simulados.
- **GREEN**: `system/tools.py`, `GET /system`, `POST /system/tools/{name}/install` y `services/system_install_tool.py`.
- **REFACTOR**: ninguno.

#### Ciclo 4: recetas [AC-2]

- **RED**: `engines/test_recipes.py` (las 9 validan; las inválidas fallan).
- **GREEN**: `engines/recipes.py` y las 9 recetas JSON con versiones y commits fijados, sacados de los venvs actuales del equipo (`uv pip freeze` de cada venv y `git rev-parse HEAD` de cada repo).
- **REFACTOR**: ninguno.

#### Ciclo 5: instalador [AC-3, AC-4, AC-5]

- **RED**: `engines/test_installer.py` y `services/test_engine_uninstall.py`.
- **GREEN**: `engines/installer.py`, `services/{engine_install,engine_uninstall}.py`, `GET /engines` y la detección de `external`.
- **REFACTOR**: ninguno.

#### Ciclo 6: verificar

- **RED**: `services/test_engine_verify.py`, con el comando armado por tipo de motor y el resultado en `settings`.
- **GREEN**: `services/engine_verify.py` y `studio engines install|verify|repair|uninstall|list`. `integration/test_venvs.py` usa la misma función.
- **REFACTOR**: ninguno.

#### Ciclo 7: pantallas [AC-8, AC-9]

- **RED**: `EngineCard.test.tsx`, `EnginesPage.test.tsx`, `StorageSettings.test.tsx` y `WelcomeWizard.test.tsx`.
- **GREEN**: `features/engines/*`, `features/settings/StorageSettings.tsx`, `features/welcome/*`, el botón «Instalar» en las opciones de Narración y Música, el banner de ffmpeg y las líneas en `nav.ts` y `es.json`.
- **REFACTOR**: ninguno.

#### Ciclo 8: e2e y docs [AC-8]

- **RED**: los e2e `engines/happy-install-verify`, `engines/neg-uninstall-external`, `welcome/happy-first-run`, `settings/happy-storage-move` y `system/neg-ffmpeg-missing`.
- **GREEN**: `_api/engines/*`, `_api/system/*` y D-8.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Modificar | `server/src/content_studio/paths.py` y todos sus usos | `unit` |
| Crear | `storage/relocate.py`, `system/tools.py`, `engines/{recipes,installer}.py`, `engines/recipes/*.json` | `unit` |
| Crear | `services/{storage_move,system_install_tool,engine_install,engine_uninstall,engine_verify}.py`, `api/routes/{engines,system,storage}.py` | `unit` |
| Modificar | `services/registry.py`, `cli/main.py`, `messages/es.json`, `integration/test_venvs.py` | `unit`, `-m local` |
| Modificar | `devtools/move_data.py` (importa `relocate`), `devtools/worktree.py` | `uv run pytest devtools -q` |
| Crear | `client/src/features/{engines,welcome}/*`, `features/settings/StorageSettings.tsx` | `client-unit` |
| Modificar | `client/src/app/{App,nav}.tsx`, `features/{narration,music}/*Options.tsx`, `client/messages/es.json` | `client-unit` |
| Crear | `tests/e2e/{engines,welcome,system}/*.e2e.ts`, `_api/{engines,system}/*` | `e2e` |
| Modificar | README de datos, `AGENTS.md`, `stack.md`, `codigo-python.md`, `worktrees.md`, `docs/process/01-done/` | `agent-context`, `rules` |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Rutas dinámicas | AC-1 | — | `unit` | [ ] |
| T2 | Reubicación | AC-7 | T1 | `unit` | [ ] |
| T3 | Herramientas del sistema | AC-6 | — | `unit` | [ ] |
| T4 | Recetas | AC-2 | — | `unit` | [ ] |
| T5 | Instalador y desinstalar | AC-3, AC-4, AC-5 | T1, T4 | `unit` | [ ] |
| T6 | Verificar y CLI | — | T5 | `unit` | [ ] |
| T7 | Pantallas | AC-8, AC-9 | T2, T3, T5, T6 | `client-unit` | [ ] |
| T8 | e2e y docs | AC-8 | T7 | `e2e`, `rules` | [ ] |
| T9 | Instalación real | AC-10 | T8 | verificación final | [ ] |

## 4. Commits

1. `refactor: rutas de datos dinámicas según almacenamiento y modo` (T1).
2. `feat: mover carpetas de datos con verificación y reescritura de rutas` (T2).
3. `feat: detectar ffmpeg, git y GPU, e instalar las herramientas con winget` (T3).
4. `feat: recetas de instalación de los motores con versiones fijadas` (T4).
5. `feat: instalar, reparar y desinstalar motores como trabajos reanudables` (T5).
6. `feat: verificar un motor con una prueba de humo y CLI studio engines` (T6).
7. `feat: pantallas Motores, Almacenamiento y bienvenida` (T7).
8. `docs: instalación desde la UI y recetas; e2e de Motores` (T8 y las fichas).
