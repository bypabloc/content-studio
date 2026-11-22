# 014: traducción real (AC-12, `-m local` con `small`)

**Qué queda.** La spec pide, para AC-12, una prueba `-m local` con el modelo `small` sobre audio en español real, además de la prueba simulada, que ya pasa.

**Por qué no se hizo en el ciclo 6.** Necesita el venv de faster-whisper, el modelo `small` descargado y el candado de la GPU (`gpu-turn`). Un audio en español real no se genera con ffmpeg, así que hay que usar una voz de `out/narration` o un fixture.

**Qué hacer.** En la verificación final (03): escribir la prueba `-m local` con `small` sobre ese audio, correrla con `python -m devtools gpu-turn run --job=014-translate -- uv run pytest -m local ...` y comprobar que `tracks.en` tiene cues en inglés sobre los mismos tramos (±0,5 s) y que `<nombre>.en.srt` existe.
