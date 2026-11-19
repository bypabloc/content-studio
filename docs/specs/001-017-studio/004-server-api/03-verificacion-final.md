# 004: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

## 1. Batería

1. `python -m devtools test-runner --type=all` y `--type=guard-tdd`.
2. `uv run pytest -m local`.
3. `uv run studio --help | cat`, `uv run studio narration tts --help | cat`, `uv run studio music --help | cat` y `uv run studio music --model foo` (exit 2) (AC-9).
4. `python -m devtools agent-context` y `rules`, más la validación headless.

## 2. Corridas reales (con el turno; AC-10)

1. CLI:
   * `python -m devtools gpu-turn run --task=004-server-api -- uv run studio narration tts --model qwen-0.6b --style expert --voice yesid --text "Prueba de la spec cuatro."`
   * `python -m devtools gpu-turn run --task=004-server-api -- uv run studio music --model acestep --style lofi-chill --duration 15`
2. API, con el server en segundo plano (`uv run studio serve --port 8765 --token t004 > logs/server-spec-004.log 2>&1`, con `run_in_background`):
   * `curl -s -H "Authorization: Bearer t004" -X POST localhost:8765/jobs -d '{"kind":"music","params":{...,"duration":15}}'` y lo mismo para la narración.
   * `curl -N "localhost:8765/events?token=t004"` en segundo plano, guardado en `tmp/spec-004/events.txt`. Tiene que mostrar `event: job` con progreso creciente.
   * Encola un tercero, cancélalo en curso y comprueba que quede `cancelled` y que `gpu-turn status` dé libre.
   * `GET /jobs`: los cuatro primeros en `done`, con `output_dir`.
   * Si el turno lo tenía otra sesión, el worker esperó sin romper nada (anótalo si pasó).
3. Duración y LUFS de las cuatro salidas. Espectrograma de una música en `tmp/spec-004/spec.png`, que revisa `image-reader` (sin voz).
4. Corta el server con Ctrl+C a mitad de un trabajo, vuelve a levantarlo y comprueba `error_code='interrupted'` (AC-11).

## 3. Escucha

Las rutas de las cuatro salidas van en el reporte. No hay que elegir entre opciones.

## 4. Cierre

* `docs/process/01-done/` con la ficha nueva `server.md` y `narration.md` y `music.md` con `studio`.
* Fichas WARNING `004-protocolo-progreso.md` y `004-token-sse.md`. Se actualiza `PENDING/002-cspell-excepciones-temporales.md` (sale `cli/` y queda `grabar/`).
* Estado de la fila 004 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con los endpoints, cómo levantar el server, los comandos `studio`, las rutas de `out/` y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 004-server-api`.
