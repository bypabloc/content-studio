# Salida de comandos — SIEMPRE ACTIVA

> En klinikae, los agentes redirigían cada corrida a mano (`> tmp/gate-g1.log`) y la raíz de `tmp/` acumulaba decenas de `.log` sueltos sin decir a qué pertenecían.

* **Audio generado**: `out/narration/` y `out/music/`, o donde indiquen `--salida` (narration) y `--carpeta` (music). No se limpian.
* **Logs de corridas**: `logs/<herramienta>-<descripción>.log` (`logs/music-heartmula-lofi.log`), en kebab-case. Nunca en la raíz de `tmp/` ni de `out/`.
* **Temporales de un comando o verificación**: `tmp/<comando>/<tema>.<ext>` (`tmp/verificar/spec.png`, `tmp/config-tests/<tema>.json`, `tmp/turno-gpu/`). Nunca `tmp/<algo>.log` suelto.
* **Corridas largas** (HeartMuLa ~5 min por pista, un lote de voces): en segundo plano (`run_in_background`), con la salida en `logs/`; el harness avisa al terminar. Nada de `sleep` en primer plano ni sondear el archivo.
* `uv run pytest` y `ruff` no se redirigen: su salida es corta y el harness la guarda.
* `out/`, `logs/` y `tmp/` están gitignoreados; el `pre-commit` rechaza cualquier archivo de ahí que se fuerce al staging.
