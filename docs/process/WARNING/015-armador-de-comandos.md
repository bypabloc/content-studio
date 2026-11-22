# 015: armador de comandos de conversión (T1)

**Qué se decidió.**

- **Catálogo como datos**: los formatos de salida están en `media/formats.py` (`TARGETS`): tipo, extensión y códec. No hay una clase por formato.
- **`build` sin ruta de salida**: `build(input_info, target, options, encoders)` devuelve los argumentos de ffmpeg sin la salida. La ruta la pone quien llama (el servicio del trabajo), así `build` es puro y se prueba con argumentos golden.
- **Códecs disponibles**: `encoders` son los códecs del ffmpeg del sistema (`system.detect()`). Uno que falta da `codec_unavailable` con su nombre.
- **Video H.264**: reusa `common/encode.video_codec` (NVENC si lo trae el ffmpeg y no se pide otra cosa; si no, libx264 con CRF 18).
- **Audio de los videos**: Opus a 128 kbps en WebM; AAC a 192 kbps en los demás contenedores.
- **Valores por defecto**: MP3 VBR V2, WAV de 16 bits, FLAC nivel 5, Ogg Opus a 128 kbps, Ogg Vorbis calidad 5, M4A a 192 kbps.

**Verificado.** `test_convert.py` (golden de cada formato de audio, video con el codificador compartido, `codec_unavailable` y `unknown_target`) y `test_formats.py`: 18 pruebas en verde.

**Dónde.** `server/src/content_studio/media/convert.py`, `media/formats.py`.
