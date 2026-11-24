# 006: el linter mira la regla 3 por párrafo y la regla 6 por la coma de la enumeración

- **Contexto**: la regla 3 pide que toda oración termine en signo, pero partir oraciones con fiabilidad pide un tokenizador. La regla 6 deja el `:` solo antes de una enumeración, y no hay forma exacta de saberlo sin un modelo. La regla 1 necesita posiciones, y `tags()` de `narration/text/segments.py` devuelve las etiquetas sin ellas.
- **Elegida**: (a) la regla 3 comprueba el final de cada párrafo (entre líneas en blanco); (b) un `:` es válido si hay una coma antes del fin de la oración («tu historial completo: consultas, antecedentes»); (c) la regla 1 reusa `MARK`, `ALIAS_KEYS` y `normalize` de `segments.py` para enmascarar las marcas de la gramática con espacios del mismo largo, y añade `(pausa)` y la notación de grabación (`/ ↗ ↘ →`), que `LABEL` no cubre; (d) `estimate_seconds` usa la velocidad de `narration/styles.py` y 0,6 s por línea en blanco (`PAUSE_PARAGRAPH`).
- **Descartadas**: duplicar las reglas en TypeScript (dos fuentes de verdad, como dice la spec); partir oraciones con un tokenizador (más código para una regla que es heurística); cambiar `tags()` para que devuelva posiciones (lo usan otros módulos).
- **Cómo revertir**: quitar `script_lint.py`, la ruta `narration.py` y su línea en `app.py`; el resto del código no depende de ellos.
- **Cómo comprobarla**: `uv run pytest server/src/content_studio/narration/script_lint.py --doctest-modules server/tests/unit/src/content_studio/narration/test_script_lint.py`.
- **Antes de**: el merge a `dev`.
