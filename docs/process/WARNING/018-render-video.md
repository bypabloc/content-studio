# 018: transformación con tamaños intermedios estables

- **Contexto**: FFmpeg falla si un `scale` o `crop` con tamaño variable por cuadro alimenta a `rotate`; no reconfigura el filtro intermedio durante el render. AC-6 también expuso un filtro `geq` con comilla sin cerrar y etiquetas intermedias repetidas.
- **Elegida**: el crop estático usa `crop`; el animado conserva el tamaño con una máscara alfa. `rotate` reserva la diagonal completa calculada desde las dimensiones de la fuente, y `scale` va después, con posición y ancla calculadas desde esas dimensiones. Las expresiones alfa cierran su cadena y cada clip usa etiquetas únicas. Así las curvas siguen el mismo grafo en la vista exacta y en la exportación.
- **Descartadas**: cambiar el tamaño antes de `rotate`, que falla en FFmpeg; transformar cada píxel del lienzo con `geq`, que evalúa más trabajo por cuadro.
- **Cómo revertir**: cambiar `editor/video_graph.py` cuando el FFmpeg compatible admita tamaños variables entre filtros; actualizar los tests de crop, escala, rotación, alfa y AC-2.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/editor/test_video_graph.py server/tests/unit/src/content_studio/editor/test_render_video.py -q` con FFmpeg disponible.
- **Pendiente**: ninguna.
