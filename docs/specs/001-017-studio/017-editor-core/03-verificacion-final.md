# 017: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. El editor nunca modifica sus entradas.

Una sola vez, con todos los commits hechos y antes del push. Ningún paso carga un modelo: no pide turno de GPU.

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e`, `--type=budget` y `--type=guard-tdd`.
2. `uv run studio editor render --help | cat`, un render real de un proyecto de fixture y `uv run studio editor render --project no-existe` (exit 2 con mensaje del catálogo).

## 2. Corridas reales en la app

1. `bun run --cwd client tauri dev`. En Editor, «Grabar» desde Inicio: graba 10 s de voz con el micrófono del equipo. Navega con el explorador hasta una música de `out/music/` (de la 011) y arrástrala a una pista nueva; suelta además un WAV desde el Explorador de Windows.
2. Mueve, recorta y divide (`S`), pon fades, baja la música 12 dB, agrega dos marcadores y prueba deshacer y rehacer. Graba una segunda toma sobre lo que suena, con auriculares.
3. Exporta a WAV y a MP3 con `podcast`, y «Exportar por marcadores».
4. Mediciones de cada salida (`verify-before-claiming-done.md` §2): duración contra la del proyecto, LUFS integrado y TP, y espectrograma en `tmp/spec-017/export-<n>.png`, que revisa `image-reader` contra «debe sonar» (sin cortes ni clics en los puntos de división).
5. Alineación de la segunda toma: la diferencia entre el transitorio de una palmada grabada y el de la pista que sonaba, medida en la exportación, es menor de 20 ms. Si no, se ajusta `editor.record_offset_ms` por defecto y se registra en `017-latencia-grabacion.md`.
6. Hash de los archivos de entrada antes y después: iguales.
7. Capturas del editor en claro y en oscuro en `tmp/spec-017/`, que revisa `image-reader`.

## 3. Escucha

Las rutas de `exports/` van en el reporte para que el usuario escuche. El gusto (volúmenes por defecto, duración de los fades) lo decide el usuario; el agente deja los valores por defecto y sigue.

## 4. Cierre

* `docs/process/01-done/editor.md`, nueva; `AGENTS.md` con la sección Editor.
* Fichas WARNING `017-proyecto-json.md`, `017-latencia-grabacion.md` y `017-preview-media-elements.md`, con su fila; `PENDING/005-desvios-d1-d8.md` actualizado (diálogo de archivos resuelto).
* Estado de la fila 017 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con las mediciones, las rutas y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 017-editor-core`.
