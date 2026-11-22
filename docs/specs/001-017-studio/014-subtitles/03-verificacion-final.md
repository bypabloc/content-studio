# 014: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. Quemar nunca modifica el video de entrada.

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e`, `--type=budget` y `--type=guard-tdd`.
2. `uv run pytest -m local` (traducción con `small` y quemado con NVENC).
3. `uv run studio subtitles --help | cat` y un caso de error (importar un `.txt` sale con exit 2 y un mensaje del catálogo).

## 2. Corridas reales (con el turno para transcribir y traducir)

1. `ffmpeg -filters | findstr subtitles`: el ffmpeg del sistema tiene libass. Si no lo tiene, prueba el flujo del error y el botón de instalación (AC-6), y anótalo.
2. **Desde un archivo**: un video vertical real (o el de la 013) con large-v3-turbo. Edita 2 cues, divide uno, marca una palabra clave con un emoji y aplica `reels`. Guarda un preset propio.
3. **Quemar** con `reels` y con `classic`. Mide la resolución, la duración y el codificador (`ffprobe`). Saca cuadros en `tmp/spec-014/frame-*.png` a tiempos con texto (`ffmpeg -ss <t> -frames:v 1`) y una captura de la vista previa JASSUB en el mismo tiempo. `image-reader` compara los dos: misma posición, fuente, color de resaltado y que el texto no caiga en la zona segura de Reels.
4. **Desde el Limpiador**: «Subtitular» sobre el resultado de la 013, sin una transcripción nueva en la cola (AC-11).
5. **Desde una narración**: una de la 006. El texto de los cues es exactamente el del guion (sin errores de whisper) y está sincronizado (escucha del usuario).
6. **Importar**: un SRT de prueba con BOM y CRLF, editar y exportar VTT.
7. **Traducir** al inglés y exportar `.en.srt`.
8. Fuentes: la lista muestra las incluidas y las del sistema, y quemar con una del sistema (Segoe UI) funciona.
9. Capturas del editor en claro y en oscuro en `tmp/spec-014/`, que revisa `image-reader`.

## 3. Revisión del usuario

Las rutas de los videos quemados (`reels` y `classic`), los SRT/VTT y la pista en inglés van en el reporte para que el usuario los vea. Si pide ajustes de gusto en los presets incluidos (tamaños o colores), se hacen en esta spec, porque son datos de `styles.py`.

## 4. Cierre

* `docs/process/01-done/subtitles.md`, nueva.
* Fichas WARNING `014-jassub.md` y `014-fuentes-ofl.md`.
* Estado de la fila 014 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con los cuadros comparados, las rutas y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 014-subtitles`.

## 6. Resultados (T8 y T9)

| Punto | Estado | Evidencia |
| :--- | :--- | :--- |
| 1. Batería | Hecho: gate `all` y e2e | e2e 44/44 (`logs/e2e-014-t8-final.log`); gate sobre el commit final (`logs/test-runner-all-014-t8-3.log`, ver `PROGRESS.md`) |
| 2. `pytest -m local` | Pendiente | `PENDING/014-traduccion-real` |
| 3. CLI `studio subtitles` | Sin efecto | `WARNING/014-sin-cli-subtitles` |
| 2. Desde un archivo con large-v3-turbo | Pendiente | `PENDING/014-capturas-editor` (no corrido en T9) |
| 3. Quemar `reels` y `classic` | Parcial: `reels` medido en T5 | 1080×1920, 3 s, amarillo al centro (`WARNING/014-quemar`); `classic` y los cuadros comparados, pendientes |
| 4. Desde el limpiador (AC-11) | Hecho | `create_main` sobre el análisis 25 y el render 26 de la 013: 75 de 76 palabras, todas dentro del audio limpio (27,25 s), inicios crecientes (`tmp/spec-014/check_t9_cleaner.py`) |
| 5. Desde una narración | Pendiente (escucha) | Alineación cubierta por tests y e2e de AC-4; la escucha es del usuario (`PENDING/014-escucha-y-revision`) |
| 6. Importar SRT con BOM y CRLF | Hecho | 2 cues con tiempos exactos y sin BOM (`tmp/spec-014/t9-import`); editar y exportar VTT cubierto por e2e |
| 7. Traducir al inglés | Hecho, salvo la prueba automatizada | whisper `small` real: 11 segmentos en inglés (`tmp/spec-014/t9-translate`); cierre a `tracks.en` con 11 cues y `.en.srt`/`.en.vtt` (`PENDING/014-traduccion-real`) |
| 8. Fuentes | Parcial | AC-8 en T4: 5 familias, Arial y Segoe UI detectadas; quemar con Segoe UI no se corrió |
| 9. Capturas del editor | Pendiente | `PENDING/014-capturas-editor` |

Verificado además: `ffmpeg` del sistema con libass (AC-6 en T5); la cola y la GPU se liberaron al terminar cada corrida real.
