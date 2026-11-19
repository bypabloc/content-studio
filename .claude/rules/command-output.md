# Salida de comandos — SIEMPRE ACTIVA

> En klinikae, los agentes redirigían cada corrida a mano (`> tmp/gate-g1.log`) y la raíz de `tmp/` acumulaba decenas de `.log` sueltos sin decir a qué pertenecían.

* **Audio generado**: `out/narration/` y `out/music/`, o donde indiquen `--output` (narration) y `--folder` (music). No se limpian.
* **Logs de corridas**: `logs/<herramienta>-<descripción>.log` (`logs/music-heartmula-lofi.log`), en kebab-case. Nunca en la raíz de `tmp/` ni de `out/`.
* **Temporales de un comando o verificación**: `tmp/<comando>/<tema>.<ext>` (`tmp/verificar/spec.png`, `tmp/config-tests/<tema>.json`, `tmp/gpu-turn/`). Nunca `tmp/<algo>.log` suelto.
* **Corridas largas** (HeartMuLa ~5 min por pista, un lote de voces): en segundo plano (`run_in_background`), con la salida en `logs/`; el harness avisa al terminar.
* **Esperar sin `sleep`**: nunca `sleep`, `Start-Sleep` ni un bucle `until …; do sleep …` en primer plano, ni sondear un archivo. Lo bloquea `.agents/hooks/shell_guard.py`, conectado en `.claude/settings.json`, `.codex/hooks.json` y `.agents/hooks.json` (Antigravity; sin probar en Codex ni Antigravity, ver `docs/process/PENDING/`). Según lo que esperas:

  | Esperas | Cómo |
  | :--- | :--- |
  | Un comando tuyo que tarda (un commit con hooks lentos, pytest, una corrida) | Lánzalo en segundo plano y espera el aviso; mientras, sigue con lo que no dependa de él |
  | La CI de un PR | `gh pr checks <n> --watch` (bloquea hasta el resultado) |
  | Una condición externa (un archivo, la GPU libre, un merge ajeno) | `Monitor` con la condición, o `CronCreate` si tarda más de 10 min |
* **Nada en WSL**: ni tests, ni instalaciones, ni reproducir la CI; es otra instancia y no interesa. Un fallo que solo da la CI (Linux) se lee con `gh run view <id> --log-failed`, se corrige aquí y se valida con el push; si no se puede comprobar antes, ficha en `docs/process/PENDING/`. Lo bloquea `.agents/hooks/shell_guard.py`.
* `uv run pytest` y `ruff` no se redirigen: su salida es corta y el harness la guarda.
* `out/`, `logs/` y `tmp/` están gitignoreados; el `pre-commit` rechaza cualquier archivo de ahí que se fuerce al staging.
