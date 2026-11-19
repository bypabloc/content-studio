# <NN>: <título en una línea>

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../process/WARNING/README.md) (ficha `<NN>-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-<NN>/` o `tmp/spec-<NN>/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

> Plantilla de [`plan-format.md`](../../../.agents/rules/plan-format.md). Al copiarla a `docs/specs/<NN>-<slug>/`, reemplaza cada `<…>`, quita esta línea y las secciones «si aplica» que no apliquen. Las rutas relativas suben un nivel más si la spec vive en un lote.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature · fix · refactor · perf · experiment · docs · chore |
| Escala | Micro (1–2 archivos) · Small (3–5) · Medium (6–10) · Large (11+) |
| Rama | `<prefijo>/<NN>-<slug>` desde `origin/dev`, en `../content-studio-worktrees/<NN>-<slug>/` |
| Depende de | `<spec>` (fusionada en `origin/dev`) · ninguna |
| Origen | Pedido del usuario · `docs/process/02-next/<NN>-<slug>.md` · `docs/research/<tema>/` |

## Objetivo

<Una o dos oraciones: qué cambia para el usuario y por qué.>

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md): precondición, contexto, decisiones, fuera de alcance, AC, «debe sonar».
* [02-plan.md](02-plan.md): ciclos TDD, archivos, tareas y commits.
* [03-verificacion-final.md](03-verificacion-final.md): batería, mediciones, cierre y PR.

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | <grupo de commits> | PEN |

## Decisiones clave

* D-1: <qué> — <por qué> (detalle en `01`).

## WARNING y PENDING

* WARNING: <fichas que deja o «ninguna»>.
* PENDING: <fichas que deja o «ninguna»>.

<!-- Escala Micro: en lugar de los otros tres archivos, agrega aquí, condensadas, las secciones «Contexto y decisión»
(con AC y fuera de alcance), «Plan» (ciclo TDD, archivos, un commit) y «Verificación final». -->
