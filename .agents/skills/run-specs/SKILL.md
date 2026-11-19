---
name: run-specs
description: >
  Ejecuta una o varias specs de docs/specs/ de principio a fin (worktree, TDD, PR, merge a dev), en secuencia, con
  reporte cada 10 minutos. Usar cuando el usuario diga "corre las specs", "ejecuta las specs 3 y 4", "run specs",
  "ejecuta el lote", o pase números o carpetas de specs para implementar.
argument-hint: "<spec> [<spec> ...]  (número, carpeta o ruta: 12 | 012-musica-cinematic | docs/specs/012-musica-cinematic)"
---

# run-specs — content-studio

## 1. Resolver las specs

1. Separa los argumentos por espacios, comas o saltos de línea; cada uno es un número, una carpeta o una ruta de `docs/specs/`. Resuélvelos con Glob (`docs/specs/<NN>-*`, también dentro de un lote).
2. Si no hay argumentos, o uno no existe o es ambiguo, lista `docs/specs/README.md` y pregunta antes de tocar nada.
3. Conserva el orden dado; si una spec depende de otra que va después, avisa y propón el orden correcto.

## 2. Ejecutar

* **Una spec**: lee todos sus archivos y el código que citan (con graphify) y ejecútala completa con la skill `execute-spec`.
* **Varias**: lee solo el `README.md` de cada una. Ejecuta la primera completa con `execute-spec`. Está terminada solo cuando su PR está fusionado en `dev` y lo comprobaste (`git fetch origin dev`, merge commit en `origin/dev`, worktree cerrado en `git worktree list`). Recién entonces pasa a la siguiente, desde el `origin/dev` que ya la contiene. Nunca dos specs a la vez. Entre una y otra, `/compact`.
* Si una spec queda `blocked` (solo `user-data`, `cost`, `credentials`, `user-stop` o `taste`, plugin `session-handoff`), deja el estado en el reporte y pregunta; no sigas con la siguiente. Fuera de eso no te detengas: los avisos de tokens no son un límite.

## 3. Reporte cada 10 minutos

Al empezar, `CronCreate` cada 10 min (`*/10 * * * *`) con el reporte; el prompt del cron termina con «Después del reporte, si PROGRESS.md no dice `Status: done` ni `Status: blocked`, sigue en el mismo turno con su `Next step`». Al terminar la última spec, o si queda `blocked`, `CronDelete`. Entrega también el reporte al cerrar cada spec.

| title | qué se hizo | en qué está | qué falta | tiempo estimado |
| :--- | :--- | :--- | :--- | :--- |

Una fila por spec (también las pendientes y las terminadas), con celdas breves sacadas de `Done`, `Current`, `Remaining` y `ETA` de `PROGRESS.md`. El tiempo es lo que falta, no lo transcurrido.

## 4. Reglas

Las de `execute-spec`, `git-workflow.md`, `worktrees.md` y `turno-gpu.md`: una spec, una rama, un worktree y un PR; nunca `--no-verify`; cero atribución de IA. El reporte final lista cada spec con su PR, su merge en `dev` y sus fichas de WARNING y PENDING.
