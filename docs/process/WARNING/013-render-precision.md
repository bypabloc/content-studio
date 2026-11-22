# 013: precisión del render de video: cuadros exactos, fps de la fuente y codificador por equipo

- **Contexto**: AC-4 exige que el primer cuadro de cada tramo sea el esperado ±1 cuadro. Al unir tramos con `trim` y `concat`, ffmpeg dejó el video a 25 cuadros por segundo aunque la fuente sea de 30 (145 cuadros en vez de 173).
- **Elegida**:
  - La tasa de cuadros sale de la fuente (`ff.frame_rate`, ffprobe) y se pasa a ffmpeg con `-r`.
  - Salida con `yuv420p` para que reproduzcan los editores y los navegadores; el original se codifica sin pérdida (`-qp 0`, `yuv444p`) solo en el fixture de la prueba.
  - Codificador: NVENC (`h264_nvenc -preset p5 -cq 19`) si el equipo tiene NVIDIA; si no, `libx264 -crf 18 -preset medium`.
  - El audio del video va en AAC a 192 kbps, igual que en el render de audio.
- **Descartadas**:
  - Dejar que ffmpeg elija la tasa: da 25 cuadros y desfasa el audio.
  - Leer el número de cuadro con OCR: el fixture lo codifica en el píxel (0, 0) con `geq`, sin ambigüedad.
  - Codificar el cuadro en la luma: el croma de yuv420p la distorsiona.
- **Cómo revertir**: quitar `-r` de `render_video` (`clean/render.py`) y el `frame_rate` de `common/ffmpeg.py`.
- **Cómo comprobarla**: `pytest server/tests/unit/src/content_studio/clean/test_render_video.py` (libx264) y `pytest -m local ...::test_ac4_nvenc_render_keeps_the_same_frames` (NVENC, en este equipo). Medición real: 173 cuadros a 30 fps; inicios de tramo en los cuadros 0, 86 y 176 (esperados 0, 86 y 176).
- **Pendiente**: nada.
