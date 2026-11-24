# 019: rasterizar títulos en el client

- **Contexto**: `drawtext` dibuja con FreeType en FFmpeg, con métricas y kerning distintos a los del navegador; mantener dos dibujos impediría la paridad de vista previa y exportación.
- **Elegida**: usar `OffscreenCanvas`, cargar fuentes de `/subtitles/fonts` y guardar el PNG con alfa en `media/text-<clip>-<sha256>.png`. El server valida el hash, el encabezado PNG, el canal alfa, dimensiones máximas de 16384 y un límite de 16 MiB. El visor y FFmpeg leen la misma imagen.
- **Presets**: `lower-third` usa Arial 48 px, blanco, contorno negro y caja semitransparente; `title-center`, Arial 96 px, blanco centrado; `caption-bold`, Arial 52 px, blanco y caja semitransparente. Los tres incluyen contorno y sombra.
- **Descartadas**: `drawtext` por diferencias de renderizado; guardar datos de texto en filtros FFmpeg porque duplica estilo y no permite que la vista previa muestre el mismo píxel.
- **Cómo revertir**: revertir el commit T2 de 019; los PNG del proyecto solo los crea el usuario al agregar títulos y no se borran automáticamente.
- **Cómo comprobarla**: `client/tests/unit/src/features/editor/text/` y las pruebas de carga en `server/tests/unit/src/content_studio/api/routes/test_editor.py`; la paridad final se comprueba en el e2e de 019.
- **Pendiente**: ninguna.
