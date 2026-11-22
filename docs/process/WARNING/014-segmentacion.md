# 014: segmentación de subtítulos

- **Contexto**: D-2 de la spec 014 pide `segment` con `min_duration`. La puntuación fuerte (. ? !) es un corte obligatorio:
  fundir un cue corto con el siguiente cruzaría esa puntuación, y AC-1 lo prohíbe con `words_per_cue`.
- **Elegida**: `segment(words, *, max_chars=42, max_lines=2, max_duration=7.0, words_per_cue=None)`. Corta siempre en la
  puntuación fuerte; en la débil (, ; :) cuando un límite lo exige; y en el límite de caracteres o de duración.
- **Descartadas**:
  - `min_duration` (fundir cues cortos): choca con el corte en la puntuación fuerte y ningún AC lo pide.
  - Cortar solo por caracteres: deja cortes a mitad de frase.
- **Cómo revertir**: `git revert` del commit de T1 (`subtitles/segment.py` y `subtitles/document.py`).
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/subtitles --doctest-modules` (AC-1, AC-5).
- **Pendiente**: si en voz rápida quedan cues de una sola palabra demasiado cortos, se revisa con la escucha del usuario.
  Es un cambio de parámetros, no de estructura.
