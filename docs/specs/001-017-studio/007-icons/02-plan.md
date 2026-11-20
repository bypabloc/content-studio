# 007: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo, con cobertura ≥ 80 % por archivo.

## 1. Ciclos TDD

#### Ciclo 1: dependencia, mapa y restricción [AC-4, AC-6]

- **RED**: `devtools/tests/unit/test_runner/test_client_lint_icons.py`: oxlint sobre una fixture que importa `lucide-react` fuera de `shared/icons.ts` falla con `no-restricted-imports` [AC-4].
- **GREEN**: `bun add --exact lucide-react@<versión de D-1>` en la raíz del workspace (como la 006: `--linker hoisted`, sin `client/node_modules` propio), `shared/icons.ts` y la regla en `client/.oxlintrc.json`.
- **REFACTOR**: ninguno.

#### Ciclo 2: IconButton y Tooltip [AC-1]

- **RED**: `shared/components/IconButton.test.tsx` y `Tooltip.test.tsx` (aria-label, aria-hidden, aria-pressed, tooltip con foco y con hover tras 400 ms, Escape, atajo).
- **GREEN**: `IconButton.tsx`, `Tooltip.tsx` e `Icon.tsx`.
- **REFACTOR**: ninguno.

#### Ciclo 3: tema y sidebar [AC-2, AC-3]

- **RED**: `app/ThemeToggle.test.tsx` (icono por modo, nombre accesible y ciclo) y `app/Sidebar.test.tsx` (colapsar, tooltips y `ui.sidebar.collapsed`).
- **GREEN**: `ThemeToggle.tsx`, `Sidebar.tsx`, `nav.ts` (campo `icon`) y las claves en `es.json`.
- **REFACTOR**: ninguno.

#### Ciclo 4: cola, paleta, Narración y Ajustes [AC-5]

- **RED**: los tests existentes de `JobRow`, `QueuePanel`, `CommandPalette`, `NarrationResult`, `CompareTakes` y `SettingsPage` pasan a buscar por `getByRole('button', { name })` y fallan mientras el botón tenga el texto visible en lugar del icono.
- **GREEN**: los botones de D-5 con `IconButton` o `Icon` + texto.
- **REFACTOR**: las clases repetidas de los botones con texto quedan en una sola constante si se repiten en tres o más archivos.

#### Ciclo 5: e2e y regla [AC-3, AC-5, AC-6]

- **RED**: `tests/e2e/shell/happy-icons-tooltips.e2e.ts` (cada botón de solo icono muestra su tooltip con el teclado), `shell/happy-sidebar-collapse.e2e.ts` y el axe ampliado en claro y oscuro.
- **GREEN**: lo que falle; D-4 escrito en `.agents/rules/ui-components.md` y `python -m devtools rules --sync`.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Modificar | `client/package.json`, `bun.lock`, `client/.oxlintrc.json` | `client-lint` |
| Crear | `client/src/shared/icons.ts`, `shared/components/{IconButton,Tooltip,Icon}.tsx` y sus tests | `client-unit` |
| Modificar | `client/src/app/{ThemeToggle,Sidebar,nav,CommandPalette}.tsx`, `features/queue/{JobRow,QueuePanel}.tsx`, `features/settings/SettingsPage.tsx`, `features/narration/*` (los de D-5), `client/messages/es.json` | `client-unit` |
| Crear | `tests/e2e/shell/{happy-icons-tooltips,happy-sidebar-collapse}.e2e.ts`; modificar `happy-apariencia-axe.e2e.ts` | `e2e` |
| Crear | `devtools/tests/unit/test_runner/test_client_lint_icons.py` y su fixture | `unit` |
| Modificar | `.agents/rules/ui-components.md`, `.agents/rules/frontend-stack.md` (versión fijada) y sus copias en `.claude/` | `rules`, `agent-context` |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Dependencia, mapa y restricción | AC-4 | — | `client-lint`, `unit` | [ ] |
| T2 | IconButton, Tooltip e Icon | AC-1 | T1 | `client-unit` | [ ] |
| T3 | Tema y sidebar | AC-2, AC-3 | T2 | `client-unit` | [ ] |
| T4 | Cola, paleta, Narración y Ajustes | AC-5 | T2 | `client-unit` | [ ] |
| T5 | e2e, axe, budget y regla | AC-3, AC-5, AC-6 | T3, T4 | `e2e`, `budget`, `rules` | [ ] |

## 4. Commits

En Conventional Commits en español; cada uno deja verde `python -m devtools test-runner --type=all`.

1. `feat: lucide-react fijado y mapa único de iconos con restricción de imports` (T1).
2. `feat: IconButton y Tooltip accesibles` (T2).
3. `feat: tema con icono y sidebar colapsable` (T3).
4. `feat: iconos en la cola, la paleta, Narración y Ajustes` (T4).
5. `test: e2e de tooltips y sidebar; criterio de iconos en ui-components` (T5).
