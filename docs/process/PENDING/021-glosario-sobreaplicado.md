# 021: «Corregir transcripción» mete términos del glosario donde el audio dice otra cosa

- **Qué**: con un glosario de nombres comunes («Agenda Clínica», «ficha del paciente», «panel de reportes») sobre una transcripción sin errores, los dos modelos proponen de 2 a 5 cambios que no corrigen nada: «la agenda de la clínica» → «la Agenda Clínica», «su ficha» → «su ficha del paciente». El prompt ya pide usar el glosario solo para una palabra mal oída y bajó Gemma de 5 a 2; Qwen sigue en 5 de 42 cues.
- **Por qué no se hizo**: el glosario es para nombres propios mal transcritos (el caso de la prueba `test_subtitles_correct`), y cada propuesta se acepta o descarta por cue. Un filtro en código (rechazar una propuesta que solo inserta un término) necesita casos reales para no esconder correcciones buenas.
- **Cuándo**: después de publicar, con transcripciones reales del usuario.
- **Quién**: agente, con ejemplos del usuario.
- **Qué la cierra**: un caso de `tests/llm_eval/cases.jsonl` con un glosario y una transcripción sin errores que pase con el ★, y el filtro si hace falta.
