# 009: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo, con cobertura ≥ 80 % por archivo.

## 1. Ciclos TDD

#### Ciclo 1: mapa de `UIIcon` [AC-1, AC-5]

- **RED**: el test de `atoms/UIIcon` con un caso por cada nombre nuevo de D-2.
- **GREEN**: los imports de lucide y las entradas del mapa en `atoms/UIIcon/index.tsx`.
- **REFACTOR**: si el mapa pasa de 300 líneas, separarlo en `UIIcon/names.ts`.

#### Ciclo 2: tema, nav, cola y paleta [AC-2, AC-3]

- **RED**:
  - Los tests de `UIThemeToggle` (icono por modo, nombre accesible y ciclo).
  - Los de `JobRow`, `QueuePanel` y `UICommandPalette` buscan por `getByRole('button', { name })` y fallan mientras el botón tenga el texto visible en lugar del icono.
- **GREEN**: `UIThemeToggle` con `theme-*`, `icon` en `NAV`, y las acciones de la cola y de la paleta con `UIIconButton`, con las claves `action.*` en los tres catálogos.
- **REFACTOR**: ninguno.

#### Ciclo 3: Narración, Ajustes, e2e y regla [AC-3, AC-4]

- **RED**:
  - Los tests de `NarrationResult`, `CompareTakes` y `SettingsPage`, por rol y nombre.
  - `tests/e2e/shell/happy-icons-tooltips.e2e.ts`: cada botón de solo icono muestra su tooltip con el teclado.
  - El axe ampliado, en claro y en oscuro.
- **GREEN**: los botones de D-5. D-4 queda escrito en `.agents/rules/ui-components.md`, y después `python -m devtools rules --sync`.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Modificar | `client/src/shared/components/atoms/UIIcon/index.tsx` y su test | `client-unit` |
| Modificar | `client/src/shared/components/molecules/UIThemeToggle/`, `organisms/UICommandPalette/`, `client/src/app/nav.ts`, `features/queue/{JobRow,QueuePanel}.tsx`, `features/settings/SettingsPage.tsx`, `features/narration/*` (los de D-5) y `messages/{es,en,pt}.json` | `client-unit`, `i18n` |
| Crear | `tests/e2e/shell/happy-icons-tooltips.e2e.ts`; modificar `happy-apariencia-axe.e2e.ts` y `happy-sidebar-collapse.e2e.ts` | `e2e` |
| Modificar | `.agents/rules/ui-components.md` y su copia en `.claude/` | `rules`, `agent-context` |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Mapa de `UIIcon` | AC-1 | — | `client-unit` | [x] |
| T2 | Tema, nav, cola y paleta | AC-2, AC-3 | T1 | `client-unit` | [ ] |
| T3 | Narración, Ajustes, e2e, axe, budget y regla | AC-3, AC-4, AC-5 | T2 | `e2e`, `budget`, `rules` | [ ] |

## 4. Commits

En Conventional Commits en español; cada uno deja verde `python -m devtools test-runner --type=all`.

1. `feat: iconos de content-studio en el mapa de UIIcon` (T1).
2. `feat: tema, nav, cola y paleta con iconos` (T2).
3. `feat: iconos en Narración y Ajustes; criterio de solo icono en ui-components` (T3).
4. `docs: cierre de la 009` (fichas, `01-done/client.md` y `git rm -r` de esta carpeta, con su fila en los dos índices).
