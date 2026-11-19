# 005: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Las versiones exactas de cada paquete (Tauri 2.x, React 19.x, Vite, Tailwind 4.x, oxlint, vitest y Playwright) se fijan al implementar con la última estable, sin rangos abiertos, y se anotan en `frontend-stack.md`.

## 1. Ciclos TDD

#### Ciclo 1: esqueleto, i18n y gates mínimos [AC-8]

- **RED**: `client/tests/unit/src/shared/i18n/t.test.ts` (clave conocida, parámetros y clave inexistente que falla en el test) y `catalog-keys.test.ts` (toda clave usada en `src/` existe en `es.json` y no sobra ninguna).
- **GREEN**: `client/` con Vite, React, TS, Tailwind v4, `index.css` (tokens zinc con violeta y Geist), oxlint, vitest, `messages/es.json` y `shared/i18n/t.ts`. `client` se agrega a los workspaces de la raíz. Etapas `client-lint`, `client-typecheck` y `client-unit` en `STAGES`.
- **REFACTOR**: ninguno.

#### Ciclo 2: API tipada y caché [AC-5 (parte de datos)]

- **RED**: `shared/api/client.test.ts` (agrega el Bearer y, ante un error `{code, message}`, lanza `ApiError` con el `message`) y `events.test.ts` (un `EventSource` simulado con `job` actualiza la caché de `['jobs']`).
- **GREEN**: `studio openapi` en el server (con su test espejo), `bun run gen:api`, `shared/api/{client,events,errors}.ts` y `Providers.tsx` con QueryClient.
- **REFACTOR**: ninguno.

#### Ciclo 3: Tauri y el server [AC-1, AC-10]

- **RED**: un test de Rust en `src-tauri/src/server.rs` (`parse_ready` lee la línea `ready`, ignora las demás y falla con timeout) y `App.test.tsx` (si `get_connection` falla, muestra la pantalla de error con Reintentar).
- **GREEN**: `src-tauri` (D-2) con los plugins, la ventana y la CSP, y `app/App.tsx` con los estados de conexión. Etapa `tauri-check`.
- **REFACTOR**: ninguno.

#### Ciclo 4: tema [AC-2]

- **RED**: `shared/theme/theme.test.ts`: `system` sigue a `matchMedia`, `light` y `dark` lo ignoran, y la caché de `localStorage` se escribe en cada cambio.
- **GREEN**: `theme.ts`, `useTheme.ts`, el script inline de `index.html`, `ThemeField.tsx` y el botón de la sidebar.
- **REFACTOR**: ninguno.

#### Ciclo 5: shell, sidebar y paleta [AC-7]

- **RED**: `app/Sidebar.test.tsx` (los grupos y entradas salen de `nav.ts` y la activa sigue al hash) y `CommandPalette.test.tsx` (filtra y navega).
- **GREEN**: `Sidebar.tsx`, `nav.ts`, `routes.ts`, `CommandPalette.tsx`, `useShortcut.ts` y los componentes de shadcn que hagan falta.
- **REFACTOR**: ninguno.

#### Ciclo 6: cola y avisos [AC-5, AC-6]

- **RED**: `features/queue/QueuePanel.test.tsx` (botones y llamadas), `useQueue.test.ts` (estado desde SSE) y `shared/notify/notify.test.ts` (toast siempre, sistema y sonido según el foco y los settings).
- **GREEN**: `QueuePanel.tsx`, `JobRow.tsx`, `useQueue.ts`, `notify.ts` y `ding.ts`, más `@dnd-kit/sortable`.
- **REFACTOR**: ninguno.

#### Ciclo 7: selector con estrella y Ajustes [AC-3, AC-4]

- **RED**: `RecommendedSelect.test.tsx` (los cuatro casos de AC-3), `SettingsPage.test.tsx` y el test del server `api/routes/test_settings.py::test_ac4_delete_prefix`.
- **GREEN**: `RecommendedSelect.tsx`, `useSetting.ts`, `features/settings/*` y `DELETE /settings?prefix=` en el server.
- **REFACTOR**: ninguno.

#### Ciclo 8: e2e, budget, CI y reglas [AC-6, AC-7, AC-9, AC-10]

- **RED**: los e2e `shell/happy-command-palette`, `shell/neg-server-down`, `queue/happy-reorder-pause-cancel-retry`, `settings/happy-theme-reset` y `settings/neg-reset-cancel`, con `_api` grabado.
- **GREEN**: `tests/e2e/` (config, `support/` con `mockApi(page)` que sirve `_api/*.json` con `page.route` y una inyección simulada de `get_connection`), las etapas `budget` y `e2e`, `budget.json`, los jobs de CI de D-9 y las reglas de D-10.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `client/**` de D-1 | `test-runner --type=client-lint,client-typecheck,client-unit` |
| Crear | `client/src-tauri/**` | `test-runner --type=tauri-check` |
| Crear | `tests/e2e/**` | `test-runner --type=e2e` |
| Modificar | `package.json` (workspaces), `bun.lock` | `bun install --frozen-lockfile` |
| Modificar | `server/src/content_studio/cli/main.py` (`openapi`), `api/routes/settings.py` (`DELETE ?prefix=`) | tests espejo |
| Modificar | `devtools/test_runner/{main,…}.py` (etapas nuevas), `devtools/worktree.py` (`bun install` y `CARGO_TARGET_DIR`) | `uv run pytest devtools -q` |
| Modificar | `.github/workflows/calidad.yml`, `.git-hooks/pre-commit`, `cspell.config.yaml`, `tests/validators/file-size.json` (excluir `schema.d.ts`) | CI |
| Crear | `.agents/rules/frontend-stack.md`, `ui-components.md` (+ las copias de `.claude/`) | `agent-context`, `rules` |
| Modificar | `testing.md`, `worktrees.md`, `command-output.md`, `graphify.md`, `AGENTS.md` | ídem |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Esqueleto e i18n | AC-8 | — | `client-unit` | [ ] |
| T2 | API tipada y SSE | AC-5 | T1 | ídem | [ ] |
| T3 | Tauri y server | AC-1, AC-10 | T2 | `tauri-check`, `client-unit` | [ ] |
| T4 | Tema | AC-2 | T1 | `client-unit` | [ ] |
| T5 | Shell y paleta | AC-7 | T1 | ídem | [ ] |
| T6 | Cola y avisos | AC-5, AC-6 | T2, T5 | ídem | [ ] |
| T7 | Selector y Ajustes | AC-3, AC-4 | T2, T5 | `client-unit`, `unit` | [ ] |
| T8 | e2e, budget, CI y reglas | AC-6, AC-7, AC-9, AC-10 | T3–T7 | `test-runner --type=all,e2e,tauri-check` | [ ] |
| T9 | App real | AC-1, AC-2 | T8 | verificación final | [ ] |

## 4. Commits

1. `feat: client con Vite, React, Tailwind v4, shadcn y catálogo es.json` (T1).
2. `feat: cliente de la API tipado desde OpenAPI y caché con SSE` (T2).
3. `feat: Tauri levanta el server con token y lo cierra con la ventana` (T3).
4. `feat: tema claro, oscuro o del sistema sin parpadeo` (T4).
5. `feat: sidebar, paleta de comandos y atajos` (T5).
6. `feat: panel de cola con reordenar, pausar, cancelar, reintentar y avisos` (T6).
7. `feat: selector con recomendado y memoria, y pantalla de ajustes` (T7).
8. `test: e2e con Playwright, budget y etapas del client en CI` (T8).
9. `docs: reglas frontend-stack y ui-components` (T8, reglas y fichas).
