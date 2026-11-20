# 018: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. El editor nunca modifica sus entradas.

Una sola vez, con todos los commits hechos y antes del push. No carga modelos de IA. NVENC no pide turno de GPU (es ffmpeg, recurso `cpu`, como en la 015).

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e`, `--type=budget` y `--type=guard-tdd`.
2. `uv run pytest -m local server/tests/unit/src/content_studio/editor` (el proyecto de 40 clips, AC-6).

## 2. Corridas reales en la app

1. `bun run --cwd client tauri dev`. Proyecto nuevo en 1080×1920 (preset `reels`): un video real del usuario (o uno de prueba grabado en `tmp/spec-018/`), un logo PNG con transparencia en una esquina que entra con un keyframe de opacidad y posición, una foto que hace zoom lento (keyframes de escala) y dos transiciones (`fade` y `slideleft`).
2. Reproduce la vista previa completa: fluida en «Calidad media» y sin saltos de sincronía con el audio.
3. Exporta a MP4 (NVENC) y a WebM. Mide la duración con `ffprobe`, el LUFS y el desvío de audio y video (una palmada visible y audible). Saca cuadros en 5 tiempos a `tmp/spec-018/export-<t>.png` y la vista previa de los mismos tiempos a `tmp/spec-018/preview-<t>.png`; los revisa `image-reader`: logo con bordes limpios (sin halo negro ni blanco), transiciones correctas y vista previa igual a la exportación.
4. Tiempo de render del proyecto de AC-6 y tamaño del `.filter`, anotados en la ficha `018-paridad-preview-export.md`.
5. Hash de los archivos de entrada antes y después: iguales.

## 3. Escucha y mirada

Las rutas de `exports/` van en el reporte. El gusto (curvas por defecto, duración de las transiciones) lo decide el usuario; el agente deja los valores por defecto y sigue.

## 4. Cierre

* `docs/process/01-done/editor.md` con la sección visual; `AGENTS.md`.
* Fichas WARNING `018-paridad-preview-export.md`, `018-proxies.md` y `018-transiciones.md`, con su fila.
* Estado de la fila 018 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con las mediciones, las rutas y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 018-editor-visual`.
