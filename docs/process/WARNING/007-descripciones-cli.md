# 007: las descripciones de motores y modelos del CLI quedan en inglés

- **Contexto**: `desc` y `note` de `engines/registry.py` (narración) y de los registros de música son la misma frase que la UI muestra en español, pero el CLI `studio` está fuera de alcance de la 007 (§4 «Fuera de alcance» de la spec 007, que queda en el historial de git).
- **Elegida**: los `desc` y `note` se quedan en inglés para el CLI. La UI lee las etiquetas de `label.*` en los tres idiomas.
- **Descartadas**:
  - Que el CLI lea el catálogo `en`: el usuario dejó el CLI fuera de esta spec.
  - Duplicar cada `desc` en el catálogo: dos fuentes de la misma frase.
- **Cómo revertir**: leer `desc` desde `label.*` en el CLI (un cambio en `cli/`), sin cambiar el catálogo.
- **Cómo comprobarla**: `uv run studio narration tts --help` sale en inglés; un test de server comprueba que cada id tenga su `label.*` en `es`.
- **Antes de**: el merge a `main`. Decidir si el CLI sale en el idioma del sistema o siempre en inglés (decisión del usuario).
