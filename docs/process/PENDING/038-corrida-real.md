# 038: corrida real con hablantes (pyannote, Limpiador y carril del Editor)

- **Qué**: la diarización real no se corrió: el motor de hablantes (pyannote) está `missing` en este equipo y su modelo en Hugging Face pide un token y aceptar su licencia, que solo tiene el usuario. Por eso quedan sin corrida real: (1) «Identificar hablantes» con un audio de dos personas (`studio diarize` y el trabajo de subtítulos); (2) el análisis del Limpiador con hablantes y «Subtitular» sobre sus cortes; (3) la captura del carril del Editor con hablantes reales. Lo que sí se verificó: el quemado real con hablantes (ASS con \1c), los exports SRT y VTT con nombres, y un proyecto sin hablantes igual que antes (con `image-reader` sobre los cuadros); los e2e cubren la pista, el interruptor y el color de la revisión.
- **Cuándo**: antes de publicar en `main`.
- **Quién**: el usuario (token de Hugging Face y licencia) y el agente (la corrida).
- **Qué lo cierra**: instalar pyannote desde Motores, correr `uv run studio diarize` sobre un audio de dos personas, crear el proyecto con «Identificar hablantes» y revisar el resultado con `image-reader`.
