# 011: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e`, `--type=budget` y `--type=guard-tdd`.
2. `uv run pytest -m local`.
3. `uv run studio music --help | cat`, `uv run studio music samples --help | cat` y `uv run studio music --model heartmula --duration 300`, que tiene que salir con exit 2 y `duration_over_max`.

## 2. Corridas reales (con el turno; las largas en segundo plano con el log en `logs/`)

1. AC-9: `python -m devtools gpu-turn run --task=011-music-section -- uv run studio music --model acestep --style lofi-jazz --duration 30`. Mide con `ffprobe` (30,00 ± 0,01) y `ebur128`, y saca el espectrograma en `tmp/spec-011/lofi-jazz.png`, que revisa `image-reader`: un fade al final, sin un bloque de silencio y sin formantes de voz.
2. Desde la UI (`tauri dev`): 2 estilos × 2 variantes de 20 s con evaluar activo. En Comparar están las 4 columnas con duración real y voz, y se elige una.
3. «Igualar a narración» con una narración de la 006 y una cola de 2 s. La pista dura la narración + 2 s.
4. Muestras: encola `music.samples` para 5 estilos (no para los 126, para no ocupar la GPU una hora). Cancela a la mitad, reanuda y comprueba que solo se generan las que faltan. Mide el tiempo por muestra y actualiza la estimación del banner.
5. HeartMuLa: una pista de 30 s en segundo plano (`logs/music-heartmula-spec-011.log`), con la misma medición de duración exacta.
6. Capturas del buscador, del texto libre y de Comparar en claro y en oscuro en `tmp/spec-011/`, que revisa `image-reader`.

## 3. Escucha

Las rutas de `lofi-jazz` a 30 s, las 4 variantes, la pista igualada a la narración y la de HeartMuLa van en el reporte. El usuario decide si el fade de 2 s suena natural. Si pide otra duración de fade, se ajusta en esta spec (es un número en `duration.py`).

## 4. Cierre

* `docs/process/01-done/music.md`, con la duración exacta, las muestras y la UI.
* Fichas WARNING `011-duracion-exacta.md` y `011-muestras.md`.
* Estado de la fila 011 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con las mediciones de duración, las rutas para escuchar, las capturas y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 011-music-section`.
