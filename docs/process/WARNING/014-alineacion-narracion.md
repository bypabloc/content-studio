# 014: alineación del guion con las palabras de whisper

- **Contexto**: el origen de narración usa el texto exacto del guion y los tiempos que whisper oyó. Whisper no escribe igual
  que el guion («una» puede salir como «un a»; alguna palabra no se oye).
- **Elegida**: `difflib.SequenceMatcher` sobre las palabras normalizadas (minúsculas, sin tildes ni signos). Las iguales
  toman su tiempo; un tramo de whisper que no cuadra en cantidad se reparte entre las palabras del guion por caracteres; las
  palabras sin par se interpolan entre sus vecinas con tiempo. Una palabra sin par al final toma 0,3 s.
- **Descartadas**: asignar por posición (se desalinea en cuanto whisper omite una palabra); alinear con un modelo de
  lenguaje (no está pedido y no hace falta: el guion es la verdad).
- **Pendiente de la escucha**: si un tramo partido por whisper sale con el tiempo repartido mal, se ve en la revisión del
  editor (T7). No cambia la estructura.
- **Cómo revertir**: `git revert` del commit de los orígenes (`subtitles/sources.py`).
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/subtitles/test_sources.py` (AC-4).
