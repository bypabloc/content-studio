# 038: corrida real de subtítulos con hablantes

- **Qué**: el proyecto de subtítulos desde la transcripción ya trae hablante en cada cue (13 cues, ninguno contradice la diarización). Falta ver en la app la vista previa y el quemado con etiqueta y color de cada hablante, y el Limpiador con hablantes sobre sus cortes.
- **Cómo cerrarlo**: `python -m devtools app-check run --scenario=subtitles` y el escenario del Limpiador, con `image-reader` sobre las capturas.
- **Cuándo**: antes de publicar en `main`.
- **Quién**: el agente.
