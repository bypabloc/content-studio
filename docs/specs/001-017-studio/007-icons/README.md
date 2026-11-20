# 007: Iconos en el client (lucide-react) y botones de solo icono

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `007-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Solo toca código del client, sus tests y las reglas de UI. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Medium (unos 10 archivos del client, más la regla de UI) |
| Rama | `feature/007-icons` desde `origin/dev`, en `../content-studio-worktrees/007-icons/` |
| Depende de | 006 (fusionada en `origin/dev`) |
| Origen | Pedido del usuario (2026-11-19), lote [001-017-studio](../README.md) |

## Objetivo

Que la UI use iconos donde un icono se entiende mejor que una palabra (el ejemplo del usuario: el cambio de tema claro, oscuro o sistema), con una sola librería, un solo componente de botón de solo icono accesible y un criterio escrito que las secciones siguientes (008 en adelante) aplican desde el primer día.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md): precondición, contexto, decisiones, fuera de alcance y AC.
* [02-plan.md](02-plan.md): ciclos TDD, archivos, tareas y commits.
* [03-verificacion-final.md](03-verificacion-final.md): batería, capturas, cierre y PR.

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | lucide-react fijado, `shared/icons.ts` y la restricción de imports | PEN |
| 2 | `IconButton` y `Tooltip` accesibles | PEN |
| 3 | Shell: tema, sidebar colapsable, paleta y cola | PEN |
| 4 | Narración (006) y Ajustes, regla de UI y e2e | PEN |

## Decisiones clave

* D-1: **lucide-react** (ISC, el set de shadcn, tree-shaking por icono, peer React ^19), con la versión exacta fijada.
* D-2: un solo mapa semántico `shared/icons.ts`; nadie más importa `lucide-react` (lo hace cumplir oxlint).
* D-3: `IconButton` con `aria-label`, tooltip propio en CSS (hover y foco) y `aria-pressed` para los conmutadores; sin Radix.
* D-4: criterio mixto: solo icono en las acciones obvias, icono y texto en la navegación y en los botones primarios.

## WARNING y PENDING

* WARNING: `007-lucide-version.md` (versión fijada y por qué) y `007-tooltip-propio.md` (tooltip en CSS en lugar de Radix).
* PENDING: ninguna.
