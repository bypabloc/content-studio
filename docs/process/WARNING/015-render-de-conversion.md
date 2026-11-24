# 015: render de conversión y GIF (T2)

**Qué se decidió.**

- **Duración medida al decodificar**: el relleno de LAME cuenta en la duración del contenedor de un MP3 (2,064 s para 2 s de audio), pero no al reproducir. AC-2 mide el tiempo que ffmpeg obtiene al decodificar (`time=` con `-f null`).
- **Opus solo a 8, 12, 16, 24 y 48 kHz**: otra frecuencia da `sample_rate_unsupported` antes de llamar a ffmpeg. El contenedor Opus reporta 48 kHz aunque se codifique a otra tasa, así que la prueba acepta ambas.
- **GIF en dos pasadas**: `palettegen` en la primera (con `stats_mode=diff`) y `paletteuse` con `dither=sierra2_4a` en la segunda, sin audio (`-an`). La paleta va junto a la salida y se borra al terminar.
- **Filtros de video**: la altura con `scale=-2:<alto>` (mantiene el aspecto y el ancho par) y los fps con `fps=`. Solo van en video; el GIF arma sus filtros en `gif_passes`.
- **Progreso**: `ffmpeg -progress pipe:1` con `-loglevel error`, y el avance sale de `out_time_ms` (en realidad microsegundos), dividido entre la duración de la fuente.
- **Calidad por defecto**: HEVC, VP9 y AV1 se codifican sin CRF ni bitrate, con los valores por defecto de ffmpeg. Se afinan en la verificación final si la vista previa lo pide.

**Verificado.** `test_convert_render.py`: los seis formatos de audio y los seis de video con ffmpeg real (códec, canales, frecuencia o resolución y duración), y el GIF de 150 cuadros a 480 px. `test_convert.py` cubre la frecuencia de Opus. 32 pruebas en `media/` en verde.

**Dónde.** `server/src/content_studio/media/convert.py` (`build`, `gif_passes`, `run`), `media/formats.py` (`TARGETS`, con `gif`).
