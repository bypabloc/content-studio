# 016: valores del ducking, salida a 48 kHz y mediciones reales (T7)

**Decisiones tomadas sin preguntar** (son un gusto, el usuario las cambia en el editor o en la spec):

- **Valores por defecto** (`server/src/content_studio/mix/project.py`, `DEFAULT_PARAMS`): ducking -12 dB, rampas de 300 ms, música -6 dB, voz 0 dB, LUFS final -14, intro y outro 0 s, unión de regiones 0,6 s, márgenes 0,2 s antes y 0,4 s después. **No se han escuchado todavía**: el gusto lo decide el usuario (`docs/process/PENDING/016-escucha-y-capturas.md`).
- **Intro y outro en 0 s** por defecto: la música se iguala a la duración de la voz, sin cola.
- **Salida a 48 kHz.** La segunda pasada de `normalize` (015) dejaba el audio a 192 kHz, porque `loudnorm` sobremuestrea para medir el pico. La mezcla salía a 192 kHz y su AAC a 96 kHz. Se corrige con `aresample=48000` al final de la cadena (commit `b459cc5`, prueba en rojo y en verde). Esto también cambia la normalización de la 015: ahora devuelve 48 kHz.
- **Techo de pico por códec**: -1 dBTP para WAV y -2 dBTP para salidas con pérdida (`normalize.true_peak_for`), porque el AAC sube el pico al codificar.
- **Video de prueba**: un clip de 30,51 s generado con ffmpeg (`tmp/spec-016/video-prueba.mp4`). `tmp/spec-013` no tiene ningún `.mp4`.

**Mediciones de las corridas reales** (jobs 7 a 10; voz `voicestudio-tonos-voxcpm2.wav`, 30,51 s; música `acestep-lofi-chill.wav`, 31 s):

| Salida | Duración | Frecuencia | Sonoridad integrada | Pico verdadero |
| :--- | :--- | :--- | :--- | :--- |
| `transcript` (`out/mix/2026-11-22-7-mix-render/mix.wav`) | 30,510 s | 48 kHz | -14,7 LUFS | -1,0 dBFS |
| `sidechain` (`out/mix/2026-11-22-8-mix-render/mix.wav`) | 30,510 s | 48 kHz | -14,8 LUFS | -1,0 dBFS |
| video `replace` (`out/mix/2026-11-22-9-mix-render/mix.mp4`) | video 30,520 s; audio decodificado 30,528 s | 48 kHz | -15,6 LUFS | -1,9 dBFS |
| video `under` (`out/mix/2026-11-22-10-mix-render/mix.mp4`) | video 30,520 s; audio decodificado 30,528 s | 48 kHz | -14,0 LUFS | -2,5 dBFS |

- **Video (AC-5, medido).** El stream de video copiado es idéntico al original en las dos salidas (md5 `f0339f32…`). El audio decodificado dura 30,528 s frente a 30,520 s del video: 8 ms, dentro de un cuadro. Los 30,60 s que da `ffprobe` en el stream AAC son el retardo de codificación (1432 tramas), que la edit list del MP4 descarta al reproducir.
- **Sonoridad: AC-3 no se cumple.** Pide -14 ± 0,5 LUFS con TP ≤ -1. Las mezclas de solo audio quedan en -14,7 y -14,8, y el video `replace` en -15,6 (techo -2). El test sintético de AC-3 pasa (16 de 16 en `mix/`), pero no cubre mezclas con picos. Detalle y reproducción: `docs/process/PENDING/016-lufs-real-fuera-de-ac3.md`.
- **Pico en el techo.** Las salidas de transcript y sidechain llegan a -1,0 dBTP, y la de `replace` a -1,9 con techo -2. Es consistente con que el techo frena la subida a -14 LUFS.
- **Espectrogramas** (`image-reader`, 48 kHz; `tmp/spec-016/mix-transcript.png` y `mix-sidechain.png`): sin recorte. Hay líneas verticales finas sobre 16–22 kHz y huecos oscuros en la banda baja; no se confirman como clics, y el ducking no se lee en la imagen. Hace falta medirlo con datos (PENDING escucha).
- **Clic en 27,9 s.** Lo vio `image-reader` en la versión de 192 kHz. En la versión de 48 kHz, la ventana de 27,85 a 27,95 s no tiene un salto aislado: tres muestras de tamaño parecido, como alta frecuencia. No se confirma como clic.

**Dónde.** `server/src/content_studio/media/normalize.py` (`second_pass`, `true_peak_for`), su test `server/tests/unit/src/content_studio/media/test_normalize.py`, y `server/src/content_studio/mix/render.py`. Salidas en `out/mix/` del worktree (gitignoreadas).
