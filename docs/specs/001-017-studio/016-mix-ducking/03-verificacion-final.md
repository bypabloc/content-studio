# 016: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. La mezcla nunca modifica las pistas de entrada.

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e`, `--type=budget` y `--type=guard-tdd`.
2. `uv run studio mix --help | cat` y `uv run studio mix --voice x.wav` (sin `--music`), que tiene que salir con exit 2 y un mensaje del catálogo.

## 2. Corridas reales

1. Desde Narración (una de la 006), «Mandar a Mezclar». En Mezcla, «Generar música para esta voz» (con el turno de GPU, en la 011) y, al terminar, «Mandar a Mezclar» desde Música.
2. Mueve una región, borra otra y agrega una. Escucha la vista previa y renderiza con `transcript`, y otra vez con `sidechain`.
3. Mediciones de las dos salidas: duración (intro + voz + outro), LUFS integrado y TP (`ebur128`). Saca el espectrograma de cada una en `tmp/spec-016/mix-<modo>.png`, que revisa `image-reader`: la música baja en los tramos de voz y no hay clipping.
4. Video: con el video de la 013, `under` y `replace`. Comprueba con `ffprobe` el stream de video copiado y la duración.
5. Capturas de la sección en claro y en oscuro en `tmp/spec-016/`, que revisa `image-reader`.

## 3. Escucha

Las rutas de la mezcla `transcript`, la `sidechain` y los dos videos van en el reporte. Los valores por defecto del ducking (-12 dB, 300 ms y -6 dB de la música) son un gusto. Si el usuario pide otros, se cambian en esta spec. Si hay varios juegos de valores para comparar, el agente deja los por defecto, registra las rutas de cada uno en `docs/process/PENDING/` y sigue.

## 4. Cierre

* `docs/process/01-done/mix.md`, nueva, y `music.md` con el enlace a la Mezcla.
* Ficha WARNING `016-valores-ducking.md`.
* Estado de la fila 016 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con las mediciones, las rutas y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 016-mix-ducking`.
