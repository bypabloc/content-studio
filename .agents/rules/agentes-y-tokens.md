---
trigger: always_on
description: Economía de tokens, subagentes (code-explorer, researcher, image-reader con Haiku), sesiones largas y varias sesiones en paralelo
---

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

* El estado entre turnos y compactaciones lo lleva el plugin `session-handoff` (solo Claude Code): sus instrucciones las inyecta él; lo propio del proyecto está en `.claude/session-handoff.json`.
* Una spec o un lote se ejecutan con `run-specs` o `execute-spec` hasta el merge de la última spec, en el mismo turno y sin pedir confirmación: ni por commits, push, merge o cierre, ni por avisos de tokens (la compactación es automática). Solo se para con una categoría de bloqueo de `.claude/session-handoff.json`; lo demás se decide y va a `docs/process/WARNING/` o `PENDING/`.
* El checkout principal no se toca durante un lote (ni `pull` con cambios locales, ni respaldos, ni instalaciones, ni borrados): cada spec sale de `origin/dev` en su worktree.
* Reporte periódico con `CronCreate` (cada 10 min) solo mientras corre una spec; se borra al terminar.

## 4. Varias sesiones en paralelo

* Cada sesión trabaja en **su worktree** (`worktrees.md`) y su rama; nunca dos sesiones en el mismo checkout ni en la misma rama.
* El recurso compartido es la GPU: **un modelo a la vez** con `gpu-turn` y avisos por `SendMessage` (`turno-gpu.md`). Lint y pytest no piden turno.
* `ListAgents` da el nombre de cada sesión; `SendMessage` solo para el turno de la GPU o una coordinación real (dos trabajos que tocan el mismo archivo), nunca para acusar recibo.
* Los merges a `dev` van de a uno: antes de fusionar, `git fetch origin dev` y merge de `origin/dev` en tu rama.
