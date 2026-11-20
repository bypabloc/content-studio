# 007: el portugués es pt-BR (Brasil), no pt genérico ni pt-PT

- **Contexto**: el catálogo en portugués lo traduce el agente. Hay que elegir variante y el código de idioma (`pt`, sin región).
- **Elegida**: `pt` con contenido de pt-BR. Es la variante de la mayor parte del público de habla portuguesa en Latinoamérica. Las etiquetas de idioma van sin región (`es`, `en`, `pt`).
- **Descartadas**:
  - pt-PT: menos público en Latinoamérica, y las formas peninsulares no coinciden con el resto del producto.
  - `pt` sin región y con mezcla de variantes: sin criterio al revisar.
- **Cómo revertir**: reemplazar las cadenas de `pt.json` por pt-PT y cambiar el diccionario de cspell (`cspell.config.yaml`, `pt-br` → `pt-pt`).
- **Cómo comprobarla**: `python -m devtools test-runner --type=spelling` pasa con `pt-br`, y la etapa `i18n` pasa con las mismas claves que `es`.
- **Antes de**: el merge a `main`. La decisión de variante es del usuario: confirmar que el público es brasileño. La revisión de las frases la cierra [PENDING 007-revision-humana-en-pt](../PENDING/007-revision-humana-en-pt.md).
