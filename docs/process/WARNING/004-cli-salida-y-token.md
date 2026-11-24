# 004: `studio` rechaza `--output` y `--folder`, y `serve` imprime el token que genera

- **Contexto**: el CLI viejo tenía `--output` (narración) y `--folder` (música). La 004 fija una sola carpeta por trabajo: `out/<herramienta>/<AAAA-MM-DD>-<id>-<slug>/`. Además, la app (spec 005) necesita el token de `studio serve` para hablar con la API.
- **Elegida**: `studio narration tts` y `studio music` salen con 2 si reciben `--output` o `--folder`; la carpeta la decide el trabajo (`params.json` dentro). Sin `--token`, `studio serve` genera uno aleatorio y lo imprime en la línea `ready`, junto al puerto. Con `--token`, no lo imprime.
- **Descartadas**: aceptar y no usar los flags (un flag que no hace nada engaña); token fijo en el código (cualquier proceso local lo adivina); imprimir siempre el token (lo escribe en logs).
- **Cómo revertir**: quitar el rechazo en `server/src/content_studio/cli/narration_params.py` y `music_params.py`; para el token, dejar de imprimirlo en `cli/serve.py`.
- **Cómo comprobarla**: `uv run studio narration tts --output x` y `uv run studio music --folder x` deben salir con 2; `uv run studio serve` muestra la línea `ready` con el token.
- **Pendiente**: la spec 005 lee el token de la línea `ready`. Si cambia su formato, se actualiza allí.
