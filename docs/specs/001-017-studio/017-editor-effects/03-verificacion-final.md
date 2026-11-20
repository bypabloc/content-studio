# 017: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. El editor nunca modifica sus entradas.

Una sola vez, con todos los commits hechos y antes del push. Solo la transcripción para crear subtítulos (011, recurso `gpu`) toma el turno de la GPU, y lo toma sola desde la cola.

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e`, `--type=budget` y `--type=guard-tdd`.
2. `uv run pytest -m local server/tests/unit/src/content_studio/editor`.

## 2. Corridas reales en la app

1. `bun run --cwd client tauri dev`. Desde un resultado de Narración, «Abrir en Editor». Suma un video con fondo verde (de prueba en `tmp/spec-017/` si el usuario no aporta uno) con chroma sobre un fondo, un `lower-third` con nombre y cargo que entra con keyframes, un tramo a 2× y otro a 0,5×, un LUT `.cube` en el video y un logo en `screen`.
2. «Agregar subtítulos» con la transcripción de la mezcla (encola `transcribe`), revisa la vista previa con JASSUB y exporta a MP4 con los subtítulos quemados.
3. Mediciones: duración con `ffprobe`, LUFS, tono de los tramos con velocidad (frecuencia fundamental del original contra la exportación), y cuadros en 5 tiempos de vista previa y exportación en `tmp/spec-017/`, que revisa `image-reader`: bordes del chroma sin halo verde, texto nítido e igual en los dos, fusión correcta y subtítulos legibles.
4. «Mandar a Normalizar» con la exportación y comprueba que Normalizar abre con la ruta.
5. Hash de los archivos de entrada antes y después: iguales.

## 3. Escucha y mirada

Las rutas de `exports/` van en el reporte. Los presets de título y los valores por defecto del chroma son un gusto: el agente deja los suyos, los registra en la ficha y sigue.

## 4. Cierre

* `docs/process/01-done/editor.md` con la sección de efectos e integración; `AGENTS.md`.
* Fichas WARNING `017-texto-rasterizado.md`, `017-fusion-con-alfa.md` y `017-chroma-paridad.md`, con su fila.
* Estado de la fila 017 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con las mediciones, las rutas y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 017-editor-effects`.
