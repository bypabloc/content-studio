# 010: revisión visual de las capturas (14 notas del image-reader)

- **Contexto**: `tmp/spec-010/` tiene 6 capturas de Mis voces, la ficha y el catálogo, en claro y en oscuro (datos sintéticos del harness). `image-reader` las revisó y dio 14 notas. Sus contrastes son estimaciones a simple vista, no mediciones.
- **Elegida**:
  - Corregida: los botones «Construir» de tarjetas con contenido distinto quedaban desalineados. Es un defecto real (commit 8bcbde9).
  - Sin cambio: los iconos sin etiqueta visible (lápiz, papelera, estrella). El criterio de solo icono (spec 009) pone `UITooltip` y `aria-label`, y eso no se ve en una captura.
  - Pendiente de medir: los contrastes del tema oscuro, en [010-contraste-tema-oscuro](../PENDING/010-contraste-tema-oscuro.md). Son tokens compartidos del design system, no de 010.
- **Descartadas**: cambiar los tokens de color desde una spec de voces. Afectaría a pantallas que 005 y 008 ya revisaron.
- **Cómo revertir**: no aplica.
- **Cómo comprobarla**: las capturas están en `tmp/spec-010/` (no se commitieron). El test temporal que las tomó se borró después de usarlo.
