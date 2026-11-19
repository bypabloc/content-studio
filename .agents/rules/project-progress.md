---
trigger: model_decision
description: Estado del proyecto y hoja de ruta en docs/process/ (01-done, 02-next, 03-later, WARNING, PENDING) y su ciclo de vida con las specs
---

# Estado del proyecto y hoja de ruta: `docs/process/`

`docs/process/` es la fuente del progreso: qué ofrece hoy content-studio, qué viene después y qué queda pendiente. Ante una consulta sobre el estado o el roadmap, empieza por [`docs/process/README.md`](../../docs/process/README.md). A diferencia de `docs/specs/` (planes efímeros), esta carpeta se mantiene con `dev`.

| Carpeta | Contenido | Estado |
| :--- | :--- | :--- |
| `01-done/` | Una ficha por módulo (narración, música, voces, CLI), hasta 40 líneas: «Qué resuelve», «Qué hace hoy», «Dónde vive», «Historial» | IMP |
| `02-next/` | Lo siguiente, una tarea por archivo `NN-<slug>.md` (prioridad = número): objetivo, alcance, qué lo habilita, dependencias, preguntas | PEN |
| `03-later/` | Planes de largo plazo, misma plantilla | PEN |
| `WARNING/` | Decisiones que tomó un agente al ejecutar y lo que hay que aplicar o revisar **antes** de pasar a `main` | PEN |
| `PENDING/` | Lo que se revisa **después** y no bloquea, con qué lo cierra | PEN |

## Ciclo de vida

1. Una idea entra como `02-next/NN-<slug>.md` o `03-later/`.
2. Al decidir implementarla, se redacta su spec en `docs/specs/` (`plan-format.md`) y, en el mismo PR, su tarea sale de `02-next/`.
3. Al fusionarse una spec funcional, su último commit actualiza la ficha del módulo en `01-done/` («Qué hace hoy», «Dónde vive», Historial y `actualizada`). Una spec técnica no toca `01-done/`.
4. Toda decisión que el agente toma solo va a `WARNING/<NN>-<tema>.md` con la plantilla de su README; lo diferido, a `PENDING/<NN>-<tema>.md`. Cada ficha se borra al aplicarla o cerrarla, en un PR a `dev`, junto con su fila del README.
