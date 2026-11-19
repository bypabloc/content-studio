# 006: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e`, `--type=budget` y `--type=guard-tdd`.
2. `uv run pytest -m local`.
3. `uv run studio narration regenerate --help | cat` y un caso de error (un trabajo inexistente sale con exit 2 y un mensaje del catálogo).

## 2. Corridas reales (con el turno)

1. App en `tauri dev`. Desde la sección Narración, con el turno tomado por la sesión (`gpu-turn status` libre, o espera según `turno-gpu.md`): un texto de 3 párrafos con un `;` (el aviso aparece y se genera igual), `voxcpm2`, `yesid`, `expert`, Evaluar activo y 1 reintento.
2. Regenera el párrafo 2 desde la UI. En Comparar, elige una toma.
3. Comprueba AC-3 sobre el disco: `sha1sum` de `blocks/0.wav` y `blocks/2.wav` de las dos tomas (iguales) y de `blocks/1.wav` (distintos).
4. Mide la duración, los LUFS y el pico de las dos tomas (`verify-before-claiming-done.md` §2). Saca el espectrograma de la toma regenerada en `tmp/spec-006/spec.png`, que revisa `image-reader` (sin cortes en los empalmes).
5. Importa dos `.json` de guion de `tmp/spec-006/` arrastrándolos: se encolan dos trabajos.
6. Capturas de la sección en claro y en oscuro en `tmp/spec-006/`, que revisa `image-reader`.

## 3. Escucha

Las rutas de las dos tomas (original y regenerada) van en el reporte para que el usuario compare los empalmes. Si el empalme se oye mal, es un fix de esta spec y no un `taste`.

## 4. Cierre

* `docs/process/01-done/narration.md`, con la UI, el linter, las tomas y regenerar.
* Fichas WARNING `006-wavesurfer.md` y `006-bloques-en-disco.md`.
* Estado de la fila 006 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con capturas, las rutas de las tomas y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 006-narration-section`.
