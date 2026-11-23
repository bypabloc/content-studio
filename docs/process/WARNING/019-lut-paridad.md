# 019: conservar el orden de muestras de las LUT `.cube`

- **Contexto**: la prueba real con FFmpeg mostró que el parser de la vista previa intercambiaba los ejes rojo y azul.
- **Elegida**: conservar el orden estándar con rojo como eje más rápido al llenar la textura 3D de WebGL.
- **Descartadas**: permutar las muestras para asumir azul como eje más rápido; la identidad y la LUT de contraste dejan de coincidir.
- **Cómo revertir**: revertir el parser de `preview/lut.ts` y quitar esta ficha de `WARNING/README.md`.
- **Cómo comprobarla**: `lut.test.ts`, los renders FFmpeg de identidad/contraste y `tests/e2e/editor/parity-effects.e2e.ts`.
- **Pendiente**: ninguna.
