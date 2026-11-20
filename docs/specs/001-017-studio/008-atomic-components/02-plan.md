# 008: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en rutas espejo, con cobertura ≥ 80 % por archivo. Los de klinikae se portan, no se reescriben: cambian los imports, se quita `'use client'` y se ajustan los textos a `t()`. Nada carga un modelo: no pide turno de GPU.

`KK` = `\\wsl.localhost\Ubuntu-24.04\home\bypabloc\projects\bypabloc\klinikae\packages`. Desde Git Bash es `//wsl.localhost/Ubuntu-24.04/home/bypabloc/projects/bypabloc/klinikae/packages`. Solo se lee y se copia, nunca se ejecuta nada ahí.

## 1. Ciclos TDD

#### Ciclo 1: base [AC-8]

- **RED**:
  - `client/tests/unit/src/styles/tokens.test.ts`: cada token de D-6, en `:root` y en `.dark`, y el contraste AA de `foreground-secondary`.
  - `client/tests/unit/src/shared/components/shadcn/smoke.test.tsx`: cada primitiva se renderiza.
- **GREEN**:
  - `bun add --exact` de las dependencias de D-1 en la raíz del workspace.
  - Revisar el paquete `cn` (D-1).
  - Copiar `KK/ui/src/shadcn/*.tsx` a `client/src/shared/components/shadcn/` y `KK/ui/src/hooks/{use-mobile,use-reduced-motion}.ts` a `client/src/shared/hooks/`.
  - `client/components.json`, `client/src/styles/{tokens,utilities}.css` y sus imports en `index.css`.
  - Fusionar `KK/app-kit/src/testing/setup.ts` en el setup de vitest del client.
  - Verify: `bun run --cwd client test -- styles shadcn` y `python -m devtools test-runner --type=client-typecheck`.
- **REFACTOR**: ninguno.

#### Ciclo 2: átomos [AC-1, AC-5]

- **RED**: portar los tests de `KK/ui/tests/unit/src/ui/<Nombre>/` de los 22 átomos de D-3 a `client/tests/unit/src/shared/components/atoms/<UINombre>/`. Sumar los de `UIBox` (`as` y `className`) y `UITooltip` (hover tras la demora, foco inmediato, Escape y atajo).
- **GREEN**:
  - Copiar cada `KK/ui/src/ui/<Nombre>/` a `atoms/UI<Nombre>/`, con sus imports a `../../shadcn/` y `@/shared/…`.
  - Adaptar `UILink` (hash) y `UIIcon` (mapa sin iconos de la clínica, más los del shell).
  - Escribir `UIBox` y `UITooltip`, y sumar a `UIStack` las props `direction`, `align` y `justify`.
  - Verify: `bun run --cwd client test -- components/atoms`.
- **REFACTOR**: ninguno.

#### Ciclo 3: moléculas [AC-1, AC-5, AC-6]

- **RED**: portar los tests de las 29 moléculas, y sumar los de `UIIconButton` (`aria-label`, `aria-pressed`, el svg con `aria-hidden` y el tooltip) y `UIRecommendedSelect` (★ en la opción recomendada y la última elección recordada, con los casos del test actual de `RecommendedSelect`).
- **GREEN**:
  - Copiar las 29 moléculas.
  - Reemplazar cada `div` y `span` interno por `UIBox`, `UIStack` o `UIText`, así ninguna molécula conserva etiquetas nativas.
  - Llevar los textos por defecto a `ui.<componente>.*` en los tres catálogos.
  - Adaptar `UIThemeToggle` al `useTheme` actual.
  - Mover `RecommendedSelect` a `molecules/UIRecommendedSelect/`.
  - Verify: `bun run --cwd client test -- components/molecules` y `python -m devtools test-runner --type=i18n`.
- **REFACTOR**: si tres o más moléculas repiten la misma estructura de label, campo y error, extraerla a un átomo (`UIFieldFrame`) y anotarlo.

#### Ciclo 4: organismos y `useForm` [AC-1, AC-5, AC-6, AC-9]

- **RED**: portar los tests de los 13 organismos y de `KK/app-kit` `useForm`, y sumar el de `UICommandPalette` (filtra, navega con flechas, abre con `Ctrl+K`, con los casos del test actual de `CommandPalette`).
- **GREEN**:
  - Copiar los organismos sin etiquetas nativas, como en el ciclo 3.
  - `UIChart` y `UIChartCard` con `lazy()` de `recharts`.
  - Dividir `UIFloatingToolbar` por responsabilidad si pasa de 300 líneas.
  - `client/src/shared/forms/useForm.ts`.
  - Mover `CommandPalette` a `organisms/UICommandPalette/`, con los ítems por props.
  - Verify: `bun run --cwd client test -- components/organisms forms` y `python -m devtools test-runner --type=budget`.
- **REFACTOR**: ninguno.

#### Ciclo 5: AppShell [AC-7]

- **RED**:
  - `organisms/UIAppShell/index.test.tsx`: nav por props, ítem activo según el hash, colapsar con botón y `Ctrl+B`, tooltips al colapsar, `ui.sidebar.collapsed` y el panel `aside`.
  - `tests/e2e/shell/happy-sidebar-collapse.e2e.ts`.
- **GREEN**:
  - `UIAppShell` adaptado (`useSectionId` y sin modo móvil).
  - `app/Shell.tsx` lo compone con `NAV`, el panel de la cola y `UIThemeToggle` al pie.
  - Borrar `app/Sidebar.tsx`, `app/ThemeToggle.tsx` y `app/CommandPalette.tsx`, con sus tests movidos a los componentes.
  - Verify: `bun run --cwd client test -- UIAppShell app` y `python -m devtools test-runner --type=e2e`.
- **REFACTOR**: ninguno.

#### Ciclo 6: migración de `features/` y `app/` [AC-7, AC-8]

- **RED**: los tests existentes de `features/queue`, `features/settings` y `features/narration`, más los e2e, se ajustan a selectores por rol y nombre accesible (`getByRole('button', { name })`). Deben seguir verdes después de migrar cada pantalla: son la red del refactor.
- **GREEN**:
  - Reescribir `JobRow`, `QueuePanel`, `SettingsPage`, las pantallas de Narración (006) y `App.tsx` solo con componentes: `UIStack`, `UICard`, `UIText`, `UIButton`, `UIIconButton`, `UISelect`, `UIField`, `UITextarea`, `UITable`, `UIDialog`, `UIStepProgress`…
  - Lo que no exista se agrega como componente en su nivel.
  - Verify: `bun run --cwd client test`, `python -m devtools test-runner --type=e2e` y el axe ampliado.
- **REFACTOR**: las clases que se repiten en tres o más pantallas pasan a una variante del componente.

#### Ciclo 7: bloqueo de etiquetas nativas [AC-2, AC-4]

- **RED**: `devtools/tests/unit/test_runner/test_ui_structure.py`, con fixtures en `devtools/tests/fixtures/ui-structure/{atoms,molecules,features,app}/`.
  - Deben fallar: `<div>`, `<button>`, `<svg>`, `createElement('span')` y `const Tag = 'h1'; <Tag>` fuera de átomos.
  - Deben pasar: lo mismo dentro de `atoms/` o `shadcn/`, `<UIStack>` y un genérico `<T,>`.
  - Más `test_ac4_precommit_runs_ui_structure`.
- **GREEN**:
  - `client/scripts/ui-structure.ts`.
  - `devtools/test_runner/ui_structure.py` y su línea en `STAGES`, `GROUPS['all']` y `FILE_STAGES`.
  - El `pre-commit` corre la etapa junto a `client-lint` cuando hay archivos de `client/` en el staging.
  - Verify: `uv run pytest devtools/tests/unit/test_runner/test_ui_structure.py -q` y `python -m devtools test-runner --type=ui-structure --git-mode=all` con 0 hallazgos.
- **REFACTOR**: si `loose-texts.ts` (007) y `ui-structure.ts` repiten la carga del programa de TS, compartir `client/scripts/ts-program.ts`.

#### Ciclo 8: jerarquía de imports y reglas [AC-3, AC-10]

- **RED**: `devtools/tests/unit/test_runner/test_client_lint_hierarchy.py`, que corre oxlint sobre fixtures: un átomo que importa una molécula, una molécula que importa un organismo, `features/` que importa `shadcn/button`, `@base-ui/react`, `lucide-react` o `UIBox`, `shared/components/` que importa `features/` y `features/` que importa `app/`. Cada uno falla; los permitidos pasan.
- **GREEN**:
  - Los `overrides` con `no-restricted-imports` en `client/.oxlintrc.json`.
  - Reescribir `ui-components.md` y actualizar `frontend-stack.md` y `devtools.md` en `.agents/`, y después `python -m devtools rules --sync`.
  - Verify: `python -m devtools test-runner --type=all`, `python -m devtools rules` y `python -m devtools agent-context`.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Modificar | `package.json`, `bun.lock`, `client/package.json` (si declara deps), `client/vite.config.ts`, `client/tsconfig.app.json`, `client/vitest.config.ts`, el setup de vitest | `client-typecheck`, `client-unit` |
| Crear | `client/components.json`, `client/src/styles/{tokens,utilities}.css`; modificar `client/src/index.css` | `tokens.test.ts` |
| Crear | `client/src/shared/components/shadcn/*.tsx` (27), `client/src/shared/hooks/{use-mobile,use-reduced-motion}.ts`, `client/src/shared/lib/cn.ts` (solo si D-1 descarta el paquete) | `client-unit` |
| Crear | `client/src/shared/components/atoms/UI*/` (24), `molecules/UI*/` (31), `organisms/UI*/` (14) y sus tests espejo, más `inventory.test.ts` | `client-unit` |
| Crear | `client/src/shared/forms/useForm.ts` y su test | `client-unit` |
| Borrar | `client/src/shared/components/RecommendedSelect.tsx`, `client/src/app/{Sidebar,ThemeToggle,CommandPalette}.tsx` y sus tests (pasan a los componentes) | `client-unit` |
| Modificar | `client/src/app/{App,Shell}.tsx`, `features/queue/*`, `features/settings/*` y `features/narration/*` | `client-unit`, `e2e` |
| Modificar | `server/src/content_studio/messages/{es,en,pt}.json` (claves `ui.*`) | `--type=i18n` |
| Crear | `client/scripts/ui-structure.ts`, `devtools/test_runner/ui_structure.py`, `devtools/tests/unit/test_runner/{test_ui_structure,test_client_lint_hierarchy}.py`, `devtools/tests/fixtures/ui-structure/**` y los fixtures de jerarquía | `uv run pytest devtools/tests/unit/test_runner -q` |
| Modificar | `devtools/test_runner/main.py`, `.git-hooks/pre-commit`, `client/.oxlintrc.json`, el baseline de `budget` | `--type=all` |
| Crear | `tests/e2e/shell/happy-sidebar-collapse.e2e.ts`; modificar los e2e de `shell/` y `settings/` | `e2e` |
| Modificar | `.agents/rules/{ui-components,frontend-stack,devtools}.md`, sus copias en `.claude/rules/` | `rules`, `agent-context` |

Cada `.tsx` y `.py` queda en 300 líneas o menos, y cada test, en 800.

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Base: dependencias, `cn`, shadcn, hooks, tokens y setup | AC-8 | — | `client-unit`, `client-typecheck` | [ ] |
| T2 | Átomos | AC-1, AC-5 | T1 | `client-unit` | [ ] |
| T3 | Moléculas y claves `ui.*` | AC-1, AC-5, AC-6 | T2 | `client-unit`, `i18n` | [ ] |
| T4 | Organismos y `useForm` | AC-1, AC-5, AC-9 | T3 | `client-unit`, `budget` | [ ] |
| T5 | AppShell y Shell | AC-7 | T4 | `client-unit`, `e2e` | [ ] |
| T6 | Migración de `features/` y `app/` | AC-7, AC-8 | T5 | `client-unit`, `e2e` | [ ] |
| T7 | Etapa `ui-structure` y pre-commit | AC-2, AC-4 | T6 | `test_ui_structure.py`, `--type=ui-structure --git-mode=all` | [ ] |
| T8 | Jerarquía en oxlint y reglas | AC-3, AC-10 | T7 | `--type=all`, `rules`, `agent-context` | [ ] |

## 4. Commits

En Conventional Commits en español, en orden. Cada uno deja verde `python -m devtools test-runner --type=all`.

1. `feat: base de componentes con Base UI, shadcn v4, tokens y setup de vitest de klinikae` (T1).
2. `feat: átomos de klinikae en shared/components/atoms` (T2).
3. `feat: moléculas de klinikae en shared/components/molecules` (T3).
4. `feat: organismos de klinikae y useForm` (T4).
5. `refactor: el shell pasa a UIAppShell con sidebar colapsable` (T5).
6. `refactor: cola, Ajustes y Narración armados solo con componentes` (T6).
7. `feat: etapa ui-structure que bloquea etiquetas HTML nativas fuera de los átomos` (T7).
8. `chore: jerarquía de Atomic Design en oxlint; reglas de componentes` (T8).
9. `docs: cierre de la 008` (fichas WARNING y PENDING, `01-done/client.md` y `git rm -r` de esta carpeta, con su fila en los dos índices).
