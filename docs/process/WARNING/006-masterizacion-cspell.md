# 006: «Masterización» es una palabra permitida de cspell en el catálogo del cliente

- **Contexto**: la opción «Avanzado» de la narración rotula la masterización de la voz en `client/messages/es.json`. El diccionario es-es de cspell no trae la palabra y el gate `spelling` falla en ese archivo.
- **Elegida**: `words: [masterización]` (minúscula: cspell distingue la forma en `words`; con mayúscula pasaba el catálogo y fallaba el comentario) en el override de `client/**` de `cspell.config.yaml` (el término aparece en el catálogo `client/messages/es.json` y en un comentario de `AdvancedOptions.tsx`), el mismo mecanismo que el alias del guion (`script_aliases.json`). Y el prop del componente se llama `supportsBatch` (no `batchable`, que cspell no reconoce).
- **Descartadas**: traducir la etiqueta («procesado final»: pierde el término que ve el usuario en el plan); agregar la palabra a `devtools/cspell/content-studio-terms.txt` (esa lista no admite español).
- **Cómo revertir**: quitar el override y cambiar la etiqueta de `narration.advanced.master`.
- **Cómo comprobarla**: `python -m devtools test-runner --type=spelling` no lista `es.json`.
- **Antes de**: el merge a `dev`.
