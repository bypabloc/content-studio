# 012: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. Ninguna herramienta modifica sus archivos de entrada.

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e`, `--type=budget` y `--type=guard-tdd`.
2. `uv run pytest -m local` (todos los codecs del ffmpeg del sistema, NVENC y YuNet).
3. `uv run studio convert --help | cat` y un caso de error por herramienta (formato inexistente, `mixed_kinds` y `reference_protected`), con exit 2 y mensaje del catálogo.

## 2. Corridas reales (sin GPU de modelos; NVENC no pide turno)

1. **Convertir**: 5 archivos reales (narraciones y músicas de las specs anteriores, más un video del usuario o el de la 010) a MP3 V2, FLAC y OGG Opus. `ffprobe` de cada salida.
2. **Redes**: el video horizontal a Reels con los 5 encuadres. Saca cuadros de cada uno en `tmp/spec-012/reels-<modo>-<t>.png` (en 3 tiempos), que revisa `image-reader`: `fit-bars` con barras, `fit-blur` con fondo desenfocado y `manual` con la zona elegida. En `follow-face`, la cara queda en el tercio central en los cuadros (AC-12).
3. **GIF** de 5 s a 15 fps: el tamaño en disco va en el reporte.
4. **Normalizar** una narración sin master (`--master no`) y una música a `podcast` y a `youtube`, con y sin «mejorar voz». La medición `ebur128` de cada salida va en el reporte. Un video normalizado conserva el stream de video (`ffprobe` con el mismo `codec_name`, bitrate y hash de paquetes con `-show_packets` resumido).
5. **Recortar** (`remove` de un tramo), **unir** 3 clips con crossfade y **dividir** cada 1 min un audio de 3 min. Mide las duraciones. Saca el espectrograma de la unión en `tmp/spec-012/concat.png`, que revisa `image-reader` (transiciones sin clic).
6. Capturas de las tres secciones en claro y en oscuro en `tmp/spec-012/`, que revisa `image-reader`.

## 3. Revisión del usuario

Las rutas de los Reels de cada encuadre, las normalizaciones (A/B con y sin mejorar voz) y la unión con crossfade van en el reporte. La cadena de «mejorar voz» es un gusto: si el usuario la quiere más suave o más fuerte, se ajusta en esta spec. Si hay que elegir entre varias cadenas, es un `blocked — taste`, con las rutas de cada opción.

## 4. Cierre

* `docs/process/01-done/convert.md` y `edit.md`, nuevas.
* Fichas WARNING `012-yunet.md` y `012-mejorar-voz.md`.
* Estado de la fila 012 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con las mediciones, los cuadros de cada encuadre, las rutas y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 012-convert-normalize-trim`.
