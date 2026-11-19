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
2. Si no hay argumentos, o uno no existe, lista `docs/specs/README.md` y pregunta antes de tocar nada. Un lote o un rango («el lote», «desde la 004») son todas sus specs pendientes en el orden del índice.
3. Conserva el orden dado; si una spec depende de otra que va después, reordena según las dependencias, anótalo en el reporte y sigue.

## 2. Ejecutar

* **Una spec**: lee todos sus archivos y el código que citan (con graphify) y ejecútala completa con la skill `execute-spec`.
* **Varias**: lee solo el `README.md` de cada una. Ejecuta la primera completa con `execute-spec`. Está terminada solo cuando su PR está fusionado en `dev` y lo comprobaste (`git fetch origin dev`, merge commit en `origin/dev`, worktree cerrado en `git worktree list`). Recién entonces pasa a la siguiente, en el mismo turno y desde el `origin/dev` que ya la contiene. Nunca dos specs a la vez. La compactación es automática: no pares para pedirla.
* **Sin pedir permiso**: el pedido del usuario ya autoriza todo el ciclo de cada spec (worktree, commits, push, PR, merge a `dev`, cierre). No preguntes «¿sigo?», «¿hago el merge?» ni «¿paso a la siguiente?». **Nunca a `main`**: ni PR `dev → main`, ni merge, ni push a `main` (tampoco `release/` ni hotfix `fix/*` a `main`) hasta que el usuario lo pida explícitamente. Cerrar una spec o un lote no lo autoriza.
* Solo para con una categoría de bloqueo de `.claude/session-handoff.json` (`user-data`, `cost`, `credentials`, `user-stop`): deja el estado en el reporte y pregunta. Todo lo demás lo decides tú, lo anotas en `docs/process/WARNING/` (crítico) o `PENDING/` (no bloquea) y sigues. Ver la tabla de §4.

## 3. Reporte cada 10 minutos

Al empezar, `CronCreate` cada 10 min (`*/10 * * * *`) con el reporte; el prompt del cron termina con «Después del reporte, si el lote no terminó ni está bloqueado, sigue en el mismo turno con la spec en curso». Al terminar la última spec, o si queda `blocked`, `CronDelete`. Al cerrar cada spec escribe su fila del reporte y **sigue en el mismo turno** con la siguiente: el turno termina solo tras la última spec o con un bloqueo válido. Un resumen al usuario a mitad del lote no es un cierre.

| title | qué se hizo | en qué está | qué falta | tiempo estimado |
| :--- | :--- | :--- | :--- | :--- |

Una fila por spec (también las pendientes y las terminadas), con celdas breves. El tiempo es lo que falta, no lo transcurrido.

## 4. Reglas

Las de `execute-spec`, `git-workflow.md`, `worktrees.md` y `turno-gpu.md`: una spec, una rama, un worktree y un PR; nunca `--no-verify`; cero atribución de IA. El reporte final lista cada spec con su PR, su merge en `dev` y sus fichas de WARNING y PENDING.

**No son motivo para parar ni preguntar** (resuélvelo, anótalo y sigue):

| Situación | Qué haces |
| :--- | :--- |
| El checkout principal tiene cambios locales, archivos sin rastrear o está atrasado | No lo tocas: ni `pull`, ni `stash`, ni mover archivos. `worktree close` solo necesita `origin/dev`; la siguiente spec sale de `origin/dev` en su worktree. Una línea en el reporte final |
| Una disyuntiva técnica, un hallazgo que cambia el alcance, una regla ambigua | Eliges la opción correcta y la registras en `docs/process/WARNING/` |
| Elegir entre audios u opciones de gusto | Eliges con el «debe sonar» de la spec, lo registras en WARNING y entregas las rutas de `out/` al final para que el usuario escuche |
| Un hook, un test o un check de CI en rojo | Diagnosticas y corriges (`fix-hooks`); tras 3 intentos sin éxito, ficha en WARNING y sigues con lo que no depende de eso |
| La GPU ocupada, CI pendiente, un merge ajeno | Esperas haciendo lo que no dependa de eso |
| Avisos de tokens, contexto o compactación | Nada: sigues con el paso siguiente |
