# 019: conservar el compuesto bajo los modos de fusión

- **Contexto**: FFmpeg consumía dos veces el stream actual al mezclar una capa y volver a componer su alfa.
- **Elegida**: dividir el stream con `split=2`; una rama calcula el color mezclado y la otra conserva el compuesto para la máscara alfa.
- **Descartadas**: referenciar el mismo stream sin dividirlo; el render perdía el fondo y las capas anteriores.
- **Cómo revertir**: revertir el cambio de `blend_graph` de T4 y quitar esta ficha de `WARNING/README.md`.
- **Cómo comprobarla**: `test_render_multiply_preserves_the_composite_under_the_blended_clip` y la paridad de los ocho modos.
- **Pendiente**: ninguna.
