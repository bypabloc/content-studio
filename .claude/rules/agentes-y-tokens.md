# Agentes, sesiones largas y economía de tokens — SIEMPRE ACTIVA

## 1. Principio

Menos tokens es más precisión. El gasto inútil sale de ciclos de prueba y error sin spec ni tests: planificar (`plan-format.md`) y probar primero (`testing.md`) ahorra más que cualquier recorte. Respuestas en viñetas cortas, tablas antes que prosa, rutas clicables.

## 2. Subagentes

| Subagente | Para qué | Modelo |
| :--- | :--- | :--- |
| `code-explorer` | Ubicar código, símbolos y archivos: graphify primero, después Glob/Grep acotados | Haiku |
| `researcher` | Tecnologías, modelos, licencias y versiones en la web, con fuentes | Haiku |
| `image-reader` | El único que abre imágenes (espectrogramas, capturas); el hook lo exige | Haiku |

* La escritura, los tests y el diagnóstico los hace la ventana principal. Ningún subagente usa Sonnet.
* Al delegar, el brief dice qué buscar, dónde y qué ya se descartó; la respuesta del subagente se contrasta antes de afirmarla.
* Un pedido mixto (una imagen y código) se reparte: la imagen a `image-reader`, la búsqueda a `code-explorer`.

## 3. Sesiones largas

* Con trabajo de más de un turno, **handoff en disco** desde el inicio (plugin `session-handoff`, configurado en `.claude/session-handoff.json`): el disco sobrevive a la compactación, el resumen no.
* Una spec o un lote se ejecutan con `run-specs` o `execute-spec` hasta el merge, sin parar por avisos de tokens. Entre una spec y la siguiente de un lote, `/compact`.
* Reporte periódico con `CronCreate` (cada 10 min) solo mientras corre una spec; se borra al terminar.

## 4. Varias sesiones en paralelo

* Cada sesión trabaja en **su worktree** (`worktrees.md`) y su rama; nunca dos sesiones en el mismo checkout ni en la misma rama.
* El recurso compartido es la GPU: **un modelo a la vez** con `turno-gpu` y avisos por `SendMessage` (`turno-gpu.md`). Lint y pytest no piden turno.
* `ListAgents` da el nombre de cada sesión; `SendMessage` solo para el turno de la GPU o una coordinación real (dos trabajos que tocan el mismo archivo), nunca para acusar recibo.
* Los merges a `dev` van de a uno: antes de fusionar, `git fetch origin dev` y merge de `origin/dev` en tu rama.
