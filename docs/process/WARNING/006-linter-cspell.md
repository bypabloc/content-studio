# 006: el linter lleva una sobrescritura de cspell en español, como el alias del guion

- **Contexto**: el spelling del pre-commit revisa las cadenas y los identificadores. El linter guarda en esas cadenas las reglas de `formato-guion.md` («formato», «guion», «pausa», «registras»), que el diccionario en inglés no conoce. El diccionario propio (`devtools/cspell/content-studio-terms.txt`) no admite palabras en español.
- **Elegida**: `cspell.config.yaml` pone `language: en,es` solo en `server/src/content_studio/narration/script_lint.py`, igual que en `script_aliases.json`. Los identificadores siguen en inglés (`ACRONYMS`, `WORD`, `REGISTRAS`).
- **Descartadas**: añadir las palabras al diccionario de términos (la configuración lo prohíbe para el español); un `# cspell:ignore` por palabra y por patrón (ensucia cada regla); traducir el texto de las reglas al inglés (la guía está en español).
- **Cómo revertir**: quitar el override de `cspell.config.yaml` y poner las palabras de las reglas en `# cspell:ignore`.
- **Cómo comprobarla**: `python -m devtools test-runner --type=spelling` no lista `script_lint.py`.
- **Antes de**: el merge a `dev`.
