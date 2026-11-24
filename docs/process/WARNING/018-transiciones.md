# 018: composición de transiciones por pista

- **Contexto**: `xfade` requiere dos flujos del mismo tamaño y tiempo base. Los clips transformados tienen tamaños y posiciones
  distintos, y el visor exacto puede pedir solo una parte de una transición.
- **Elegida**: cada clip de la transición se compone sobre un lienzo transparente del tamaño del proyecto; se encadenan con
  `xfade` según el solapamiento validado y luego se recorta el flujo al rango solicitado. La pista conserva su alfa al
  superponerse sobre las pistas inferiores. Las transiciones usan los filtros nativos de FFmpeg: `fade`, `fadeblack`,
  `fadewhite`, `wipeleft`, `wiperight`, `slideleft`, `slideright` y `circleopen`.
- **Descartadas**: aplicar `xfade` a las fuentes originales, porque no comparten tamaño ni posición; dibujar ambos clips
  por separado, porque el superior taparía al inferior durante el solapamiento.
- **Cómo revertir**: `git revert 0a35e9b`; retira el compositor y sus pruebas de transición.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/editor/test_render_video.py
  server/tests/unit/src/content_studio/editor/test_video_transitions.py -q`. AC-6: 40 clips, 60 s a 720p/30 fps, NVENC,
  render en 6,18 s y grafo de 26 395 bytes.
- **Pendiente**: ninguna.
