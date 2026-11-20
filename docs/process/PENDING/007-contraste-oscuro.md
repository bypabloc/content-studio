# 007: el texto del botón primario en tema oscuro tiene poco contraste

- **Qué**: en la revisión visual de las capturas de Narración en oscuro (en, pt y es), el texto del botón «Generar» (`bg-primary text-primary-foreground`) se ve oscuro sobre un morado apagado, con poco contraste.
- **Por qué no se hizo**: el problema viene del tema de la 005 (tokens de color), no de los textos de la 007. Axe en tema oscuro no reporta fallos serios, así que la prueba automática no lo marca.
- **Cuándo**: después de la 007.
- **Quién**: agente.
- **Qué la cierra**: medir la razón de contraste del botón en oscuro (WCAG AA, 4,5:1 para texto normal) y, si no llega, ajustar el token `--primary-foreground` o `--primary` en `client/src/index.css`, con una captura nueva revisada por `image-reader`.
