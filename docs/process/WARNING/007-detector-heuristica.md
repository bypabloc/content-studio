# 007: el detector de textos sueltos usa una heurística, no un análisis de lenguaje

- **Contexto**: hay que decidir qué literal cuenta como texto visible en Python (con `ast`) y en TS (con el compilador de TypeScript), sin depender de una librería de lenguaje.
- **Elegida**: un literal cuenta si, sin los espacios del borde, tiene al menos una letra y cumple una de estas condiciones: dos palabras con letras separadas por espacio; una letra fuera de ASCII (á, ñ, ç, ã) o `¿`/`¡`; una sola palabra con mayúscula inicial y el resto en minúsculas (`'Cancelar'`). Los ids, las claves, las constantes, los nombres en PascalCase y los atajos no cuentan. Las excepciones son la lista `allowed` de `tests/validators/i18n.json` y el marcador `i18n-ignore: <motivo>`.
- **Descartadas**:
  - `react/jsx-no-literals`: marca `className` y no ve los literales fuera del JSX.
  - Un grep de palabras en español: no ve el inglés ni el portugués, y falla con los acentos.
  - Un baseline de textos sueltos: el repo queda en cero al cerrar la 007, así que no hay nada que congelar.
- **Cómo revertir**: quitar la etapa de `GROUPS['all']` y del pre-commit; el resto no depende de ella.
- **Cómo comprobarla**: `python -m devtools test-runner --type=i18n --git-mode=all` da 0 hallazgos; `devtools/tests/unit/test_runner/test_i18n_loose.py` pasa.
- **Qué deja pasar**: una sola palabra en minúsculas en inglés (`ok`) no se marca; un texto que parece identificador sí se puede ocultar con el marcador, con su motivo.
- **Antes de**: el merge a `main`. Revisar la lista `allowed` y los marcadores que quedaron: hoy hay uno, en `client/src/features/narration/ScriptHighlight.tsx` (clases de Tailwind).
