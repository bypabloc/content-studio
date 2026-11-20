# 008: Componentes con Atomic Design traídos de klinikae, y sin etiquetas HTML nativas fuera de los átomos

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `008-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Solo toca código del client, sus tests, devtools, hooks y reglas. **klinikae se lee y no se modifica**: se copia desde `\\wsl.localhost\Ubuntu-24.04\home\bypabloc\projects\bypabloc\klinikae\packages\` y nada corre en WSL. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | refactor · feature |
| Escala | Large (unos 64 componentes, 27 primitivas de shadcn, tokens, `useForm`, el shell, las pantallas actuales, una etapa nueva de devtools y reglas) |
| Rama | `feature/008-atomic-components` desde `origin/dev`, en `../content-studio-worktrees/008-atomic-components/` |
| Depende de | [007](../007-i18n/README.md) (fusionada en `origin/dev`): los componentes reciben sus textos del catálogo único |
| Origen | Pedido del usuario (2026-11-19), lote [001-017-studio](../README.md) |

## Objetivo

Toda la UI del client se arma con componentes reutilizables en tres niveles de Atomic Design: átomos, moléculas y organismos, en `client/src/shared/components/`. Los templates viven en `client/src/features/` y las páginas, en `client/src/app/`.

Los componentes llegan de klinikae (`packages/ui` y `packages/app-kit/src/forms`). Ya están probados y son más escalables que los controles HTML de hoy: Select con estrategia según la cantidad de opciones, SearchSelect y Combobox con búsqueda, DateRangePicker con presets, Table, Dialog, FileDrop, Chart y AppShell con sidebar colapsable.

Una etiqueta HTML nativa (`div`, `button`, `input`…) fuera de un átomo, o un import que salte la jerarquía, no pasa el `pre-commit` ni la CI.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md): precondición, contexto, inventario de klinikae, decisiones, clasificación por nivel, fuera de alcance, AC y diagrama.
* [02-plan.md](02-plan.md): ciclos TDD, archivos, tareas y commits.
* [03-verificacion-final.md](03-verificacion-final.md): batería, app real, cierre y PR.

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Base: dependencias, `cn`, tokens y utilidades, primitivas de shadcn, setup de vitest | PEN |
| 2 | Átomos (22 de klinikae, más `UIBox` y `UITooltip`) | PEN |
| 3 | Moléculas (29 de klinikae, más `UIIconButton` y `UIRecommendedSelect`) | PEN |
| 4 | Organismos (13 de klinikae, más `UICommandPalette`) y `useForm` | PEN |
| 5 | AppShell y migración de `app/` y `features/` (shell, cola, Ajustes, Narración) | PEN |
| 6 | Bloqueo: etapa `ui-structure` (etiquetas nativas) y oxlint (jerarquía de imports) en el `pre-commit` y en `all`, y reglas | PEN |

## Decisiones clave

* D-1: `@base-ui/react` + shadcn v4, con las versiones exactas de klinikae. Las primitivas de shadcn van a `shared/components/shadcn/`.
* D-2: `atoms/`, `molecules/` y `organisms/`, con una carpeta por componente (`atoms/UIButton/index.tsx`) y prefijo `UI`, igual que klinikae.
* D-3: entran los 64 componentes genéricos de klinikae. Quedan fuera los de la clínica, autenticación, web pública y encuestas, y `UserMenu` y `BottomNav`.
* D-4: jerarquía estricta. Las etiquetas nativas solo van en `shadcn/` y `atoms/`. Una molécula solo usa átomos y moléculas; un organismo, además, organismos. `features/` y `app/` solo usan componentes.
* D-5: las etiquetas nativas las bloquea un script con el compilador de TypeScript (etapa `ui-structure`); la jerarquía de imports, `no-restricted-imports` de oxlint por carpeta.
* D-6: los tokens y utilidades de klinikae (`ui-focus`, `ui-press`, tipografías, sombras, `foreground-secondary`, `primary-hover`…) se adaptan al tema claro, oscuro y sistema de content-studio.
* D-7: `AppShell` reemplaza al Shell y la Sidebar actuales, con el router por hash y sin `next/navigation`. La sidebar colapsable sale de aquí, y la 009 ya no la hace.
* D-8: de `app-kit` entran `forms/useForm` y `testing/setup`; `build/` no aplica a Tauri.

## WARNING y PENDING

* WARNING: `008-base-ui-shadcn.md` (D-1 y versiones), `008-excluidos-de-klinikae.md` (D-3), `008-ui-box.md` (D-4: el átomo genérico solo para componentes), `008-tokens-adaptados.md` (D-6), `008-appshell.md` (D-7), `008-paquete-cn.md` (D-1) y `008-budget.md` (D-9: el delta real del bundle).
* PENDING: `008-sincronizar-con-klinikae.md` (cómo traer las mejoras de klinikae a futuro, sin paquete compartido).
