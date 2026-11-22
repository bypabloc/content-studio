# 014: traducción real (AC-12, `-m local` con `small`)

**Hecho y verificado a mano (T9).** Traducción real con `transcribe_main --task translate --model small` sobre un clip de 40 s en español (`charla-corta-40s.mp4`, bajo `gpu-turn`): 11 segmentos en inglés con tiempos coherentes (`tmp/spec-014/t9-translate/words.json`, log `logs/subtitles-translate-014-t9.log`). Cierre del worker (`translate.finish`): `tracks.en` con 11 cues y `charla-bom.en.srt` / `.en.vtt` escritos.

**Qué queda.** La prueba automatizada `-m local` (pytest) que repite esa corrida con un audio de fixture, y el chequeo de que los cues en inglés caen sobre los mismos tramos que el español (±0,5 s) en un proyecto real.

**Por qué no está automatizada.** El audio en español real no se genera con ffmpeg, y la prueba necesita el venv de faster-whisper, el modelo `small` y el candado de la GPU.

**Qué hacer.** Escribir la prueba `-m local` con un fixture de voz, correrla con `python -m devtools gpu-turn run --job=014-translate -- uv run pytest -m local ...`.
