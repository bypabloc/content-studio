# 009: Iconos aplicados en la UI y criterio de solo icono

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `009-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Solo toca código del client, sus tests y las reglas de UI. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Medium (unos 8 archivos del client, más la regla de UI) |
| Rama | `feature/009-icons` desde `origin/dev`, en `../content-studio-worktrees/009-icons/` |
| Depende de | 008 (fusionada en `origin/dev`) |
| Origen | Pedido del usuario (2026-11-19), lote [001-017-studio](../README.md) |

## Objetivo

Que la UI use iconos donde un icono se entiende mejor que una palabra. El ejemplo del usuario es el cambio de tema claro, oscuro o sistema. Las piezas ya las trae la 008: `UIIcon` (lucide-react), `UIIconButton`, `UITooltip` y la sidebar colapsable de `UIAppShell`. Esta spec suma los iconos que faltan al mapa de `UIIcon`, escribe el criterio de cuándo usar solo icono y lo aplica al tema, la cola, la paleta, Narración y Ajustes. Así, las secciones de la 010 en adelante lo aplican desde el primer día.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md): precondición, contexto, decisiones, fuera de alcance y AC.
* [02-plan.md](02-plan.md): ciclos TDD, archivos, tareas y commits.
* [03-verificacion-final.md](03-verificacion-final.md): batería, capturas, cierre y PR.

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Iconos de content-studio en el mapa de `UIIcon` | PEN |
| 2 | Tema, nav, cola y paleta con iconos | PEN |
| 3 | Narración (006) y Ajustes, regla de UI y e2e | PEN |

## Decisiones clave

* D-1: lucide-react, `UIIcon`, `UIIconButton`, `UITooltip` y la sidebar colapsable ya los trae la 008. Esta spec no suma librerías ni componentes base.
* D-2: un solo mapa de nombres, el de `UIIcon`, con un icono por acción en toda la app. Nadie fuera de `shared/components/` importa `lucide-react` (lo bloquea la 008).
* D-4: criterio mixto: solo icono en las acciones obvias, icono y texto en la navegación y en los botones primarios.

## WARNING y PENDING

* WARNING: `009-iconos-sustitutos.md` (si algún nombre del mapa no existe en la versión de lucide que fijó la 008 y se usa otro).
* PENDING: ninguna.
