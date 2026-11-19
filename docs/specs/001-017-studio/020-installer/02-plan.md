# 020: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo (Python, TS y Rust con `cargo test`), con cobertura ≥ 80 % por archivo en Python y TS.

## 1. Ciclos TDD

#### Ciclo 1: modo instalado [AC-1]

- **RED**: `src-tauri/src/bootstrap.rs::tests::detect_mode` y `test_paths.py::test_ac1_resources_env`.
- **GREEN**: `detect_mode()` y la propagación de las variables de entorno al server. `paths.resources_dir()`.
- **REFACTOR**: ninguno.

#### Ciclo 2: siembra [AC-2]

- **RED**: `test_seed.py` (vacío, sin cambios, modificado → `.new` y referencias protegidas).
- **GREEN**: `content_studio/seed.py` y `studio seed`.
- **REFACTOR**: ninguno.

#### Ciclo 3: respaldo y migraciones al actualizar [AC-3]

- **RED**: `db/test_schema.py::test_ac3_backup_restore`.
- **GREEN**: el respaldo y la restauración en `db/schema.py` y la rotación de 5.
- **REFACTOR**: ninguno.

#### Ciclo 4: bootstrap en Rust y pantalla de preparación [AC-5]

- **RED**: `bootstrap.rs::tests` (pasos idempotentes con un ejecutor simulado y errores) y `client/tests/unit/src/bootstrap/BootstrapPage.test.tsx`.
- **GREEN**: `bootstrap.rs`, la ventana `splash`, `client/src/bootstrap/*` y las claves `bootstrap.*` en `es.json`. `server.rs` usa el python del venv de la app en modo instalado.
- **REFACTOR**: ninguno.

#### Ciclo 5: versión [AC-4]

- **RED**: `devtools/tests/unit/test_version.py`.
- **GREEN**: `devtools/version.py` y su línea en `COMANDOS`. La etapa `validators` corre `version --check`.
- **REFACTOR**: ninguno.

#### Ciclo 6: NSIS y recursos [AC-6]

- **RED**: un test de devtools que valida `tauri.conf.json` (`installMode`, idioma, recursos y la lista de exclusión de venvs y modelos).
- **GREEN**: `bundle` en `tauri.conf.json`, `installer/nsis/{hooks,strings-es}.nsh`, un script de build `devtools/fetch_uv.py` (descarga `uv.exe` fijado con su sha256 a `client/src-tauri/bin/`, que está gitignoreado) y la exportación del lock del server.
- **REFACTOR**: ninguno.

#### Ciclo 7: updater [AC-9]

- **RED**: `features/settings/AboutSettings.test.tsx` y `shared/update/useUpdater.test.ts` (simulado: ofrece actualizar, espera a que no haya trabajos y llama a `downloadAndInstall` y `relaunch`).
- **GREEN**: `tauri-plugin-updater` y `plugin-process`, `useUpdater.ts`, Ajustes > Acerca de, y la `pubkey` en `tauri.conf.json`.
- **REFACTOR**: ninguno.

#### Ciclo 8: workflow de release y docs [AC-10]

- **RED**: `release.yml` con un `workflow_dispatch` `dry-run` corrido en la rama, que tiene que fallar con un tag distinto y compilar sin publicar con uno correcto.
- **GREEN**: `.github/workflows/release.yml`, `docs/operations/release.md` y D-9.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `client/src-tauri/src/bootstrap.rs`, `client/src/bootstrap/*`, `client/src-tauri/installer/nsis/{hooks,strings-es}.nsh` | `tauri-check`, `cargo test`, `client-unit` |
| Modificar | `client/src-tauri/{tauri.conf.json,Cargo.toml,src/lib.rs,src/server.rs,capabilities/default.json}` | ídem |
| Crear | `server/src/content_studio/seed.py`, `client/src/shared/update/useUpdater.ts`, `features/settings/AboutSettings.tsx` | `unit`, `client-unit` |
| Modificar | `server/src/content_studio/{paths.py,db/schema.py,cli/main.py,messages/es.json}`, `client/messages/es.json` | `unit` |
| Crear | `devtools/{version,fetch_uv}.py` y sus tests | `uv run pytest devtools -q` |
| Modificar | `devtools/test_runner/validators.py`, `.gitignore` (`client/src-tauri/bin/`) | ídem |
| Crear | `.github/workflows/release.yml`, `docs/operations/release.md` | `dry-run` |
| Modificar | `AGENTS.md`, `git-workflow.md`, `devtools.md`, `frontend-stack.md`, `docs/process/01-done/` (+ `installer.md`) | `agent-context`, `rules` |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Modo instalado | AC-1 | — | `cargo test`, `unit` | [ ] |
| T2 | Siembra | AC-2 | T1 | `unit` | [ ] |
| T3 | Respaldo y migraciones | AC-3 | — | `unit` | [ ] |
| T4 | Bootstrap | AC-5 | T1, T2 | `cargo test`, `client-unit` | [ ] |
| T5 | Versión | AC-4 | — | `uv run pytest devtools -q` | [ ] |
| T6 | NSIS y recursos | AC-6 | T4 | test de configuración | [ ] |
| T7 | Updater | AC-9 | T6 | `client-unit` | [ ] |
| T8 | Release y docs | AC-10 | T5–T7 | `dry-run` | [ ] |
| T9 | Instalación real | AC-6, AC-7, AC-8, AC-9 | T8 | verificación final | [ ] |

## 4. Commits

1. `feat: detectar el modo instalado y pasar los recursos al server` (T1).
2. `feat: sembrar los datos de la app sin pisar los del usuario` (T2).
3. `feat: respaldo de la base antes de migrar al actualizar` (T3).
4. `feat: primer arranque con uv y pantalla de preparación` (T4).
5. `chore: devtools version sincroniza la versión en todos los manifiestos` (T5).
6. `feat: instalador NSIS por usuario en español, conservando los datos al desinstalar` (T6).
7. `feat: actualizaciones automáticas desde GitHub Releases` (T7).
8. `ci: workflow de release en tags v*; docs de publicación` (T8 y las fichas).
