# 014: quemar subtítulos (ciclo 5)

**Qué se decidió.**

- **Libass se comprueba dos veces.** `subtitles.burn` rechaza al encolar con `ffmpeg_no_libass` (`validate`, vía `system.detect()['subtitles_filter']`, que mira `ffmpeg -filters`). Si el ffmpeg cambia mientras el trabajo espera, `burn_main` sale con código 3 y el servicio lo traduce a `ffmpeg_no_libass` (`ERROR_CODES`). La primera comprobación evita crear un trabajo que no puede correr.
- **Fuentes**: `fontsdir` apunta a `server/data/fonts`, sin carpeta temporal con enlaces (D-7 la proponía). Libass lee las fuentes incluidas desde ahí y las del sistema las encuentra por su cuenta.
- **Estilo**: con `preset` se usa el preset; sin él, el estilo del documento sobre el clásico (un documento nuevo trae `style: {}`).
- **Verificado**: AC-6 con ffmpeg real. Un vertical de 1080×1920 de 3 s sale con la misma resolución y duración, y el centro tiene píxeles del amarillo de resaltado. Libass resuelve `Montserrat ExtraBold` con `fontsdir` (la pregunta abierta en el handoff queda cerrada).
- **Codificador**: `video_codec` pasa a `common/encode.py` y `clean/render.py` lo importa. Las pruebas de 013 siguen en verde.
- **Recurso `cpu`**: es ffmpeg, no carga modelos. NVENC no toma el candado de la GPU.
- **Salidas**: `subtitles.ass` y `subtitled.mp4` en la carpeta del trabajo.
- **Datos del trabajo**: `prepare` completa `doc` y `source` a partir del proyecto. Así el comando no abre la base.

**Dónde.** `subtitles/burn.py`, `subtitles/burn_main.py`, `services/subtitles_burn.py`, `common/encode.py`, `common/ffmpeg.py` (`video_size`), `system/tools.py` (`subtitles_filter`), `messages/*.json` (`burn_needs_video`, `ffmpeg_no_libass`).
