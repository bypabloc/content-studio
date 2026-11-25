# 037: corrida real de la sección Hablantes

- **Qué**: falta mirar en la app que las regiones de la línea de tiempo coincidan con los turnos de un clip de dos personas. La diarización da esos turnos (DER 10,5 % sin collar, 9,2 % con collar de 0,25 s) y los subtítulos y la transcripción coinciden con ella.
- **Cómo cerrarlo**: `python -m devtools app-check run --scenario=speakers` y revisar con `image-reader`.
- **Cuándo**: antes de publicar en `main`.
- **Quién**: el agente.
