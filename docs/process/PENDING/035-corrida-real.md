# 035: corrida real del trabajo de hablantes

- **Qué**: falta un clip real de dos personas cortado por hablante con la API (`diarize.split`) y que escuches cada `speakers/*.wav`. Lo demás ya se hizo: `studio diarize` corre con pyannote en dos clips de muestras de voz (50 s) y en montajes de 30 y 60 min; el pico de VRAM (1,1 GB de pyannote sobre la línea base) y el WDER de la transcripción con hablantes (0,0 % en dos voces y en tres) están en `docs/research/diarizacion-pyannote/10-pruebas-en-gpu.md`.
- **Cómo cerrarlo**: tú escuchas los `speakers/*.wav` de un clip real con dos personas y confirmas que cada archivo tiene solo a su hablante.
- **Cuándo**: antes de publicar en `main`.
- **Quién**: el usuario (escucha).
