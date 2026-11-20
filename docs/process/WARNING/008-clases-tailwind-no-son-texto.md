# 008: una lista de clases de Tailwind no cuenta como texto visible en el detector TS

- **Contexto**: la etapa `i18n` (007) marca como texto suelto cualquier literal con dos palabras separadas por espacio. Las primitivas de shadcn y los variantes de `cva` tienen cientos de cadenas como `bg-primary text-primary-foreground hover:bg-primary/80`: pasan la regla y no son texto, y el detector las marcaba (32 hallazgos en la primera corrida).
- **Elegida**: `isClassList` en `client/scripts/loose-texts.ts`. Un literal es una lista de clases si todos sus trozos son minúsculas ASCII (con `-`, `:`, `[`, `]`, `/`, `!`, `.`, `%`, `(`, `)`, `,`, `#`, `*`, `&`, `@`, `'`, `"`, `=`, `+`, `>`, `~`, `^`, `$`, `|` y `\`) y al menos uno tiene una marca de utilidad (`-`, `:`, `[`, `]`, `/`, `!`, `*`, `&`, `@`). Así `cn('...')`, `cva(...)` y `variants: { default: '...' }` no se marcan, y las excepciones de 007 (`className`, `cn`, `clsx`, `cva`) siguen igual.
- **Descartadas**:
  - Ignorar `variants` o `classNames` por nombre de propiedad: es una lista que hay que mantener, y `toastOptions.classNames` no sale de ahí.
  - Excluir la carpeta de shadcn del detector: taparía también los textos reales que una primitiva pudiera traer (un `sr-only` en inglés, por ejemplo). Con la regla, esos textos siguen marcándose.
- **Qué deja pasar**: una frase en minúsculas que tenga un guion en un trozo y solo trozos ASCII (`save-the-day now`). En la UI los textos llevan mayúscula inicial o tilde, así que no es un caso real; queda anotado.
- **Cómo revertir**: quitar la condición `!isClassList(value)` de `visit` en `client/scripts/loose-texts.ts`; las 32 cadenas volverían a marcarse.
- **Cómo comprobarla**: `uv run pytest devtools/tests/unit/test_runner/test_i18n_loose.py` (la prueba `test_ac5_class_strings_in_variant_maps_are_not_text` falla sin la regla y pasa con ella) y `python -m devtools test-runner --type=i18n --git-mode=all` con 0 hallazgos.
- **Antes de**: el merge a `dev`.
