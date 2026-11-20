# 010: el progreso del build cuenta cada estilo una vez, y cada voz ocupa un tramo del trabajo

- **Contexto**: AC-7 pide que el progreso llegue por SSE por estilo. Una voz genera hasta 12 estilos en rondas, y una ronda puede repetir un estilo que no aprobó. Un trabajo con varias voces necesita una sola barra de progreso.
- **Elegida**: `voices/main.py` reparte el trabajo en tramos iguales, uno por voz. `build()` emite un `@@progress` cada vez que un estilo queda evaluado por primera vez (`span_fraction`, en `common/progress.py`), y uno al cerrar la voz con el fin de su tramo. Las etiquetas van en inglés y en ASCII (`yesid: friendly`), igual que las del resto de los motores.
- **Descartadas**: contar cada evaluación (el progreso retrocedería o pasaría de 1 al repetir una ronda); emitir solo el fin de cada voz (AC-7 pide progreso por estilo).
- **Cómo revertir**: quitar los `progress.emit` de `build()` y el parámetro `span`; `main()` vuelve a llamar `build(n, cat[n], force)`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/services/test_voice_build.py` (un build simulado emite cuatro pasos para dos voces, sube sin retroceder y termina en 1) y los doctests de `span_fraction`.
- **Pendiente**: ninguno. La salida real con CosyVoice se mira en la T9.
