# 019: valores iniciales del chroma y paridad

- **Contexto**: el Inspector necesita valores iniciales útiles; FFmpeg y WebGL calculan la distancia del color clave con fórmulas distintas.
- **Elegida**: iniciar con verde `#00ff00`, `similarity=0.2` y `blend=0.1`; validar el sujeto rojo sobre el fondo azul con el render FFmpeg y SSIM >= 0,95.
- **Descartadas**: duplicar la imagen del chroma en la exportación o afirmar equivalencia por las fórmulas sin comparar cuadros reales.
- **Cómo revertir**: revertir T4 y quitar esta ficha de `WARNING/README.md`.
- **Cómo comprobarla**: `test_render_chroma_replaces_green_and_preserves_red_subject` y `tests/e2e/editor/parity-effects.e2e.ts`.
- **Pendiente**: ninguna.
