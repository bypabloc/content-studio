# 036: corrida real con hablantes (pyannote) y revisión de capturas con hablantes

- **Qué**: la corrida real de «Identificar hablantes» con un clip de dos personas: los nombres en el texto (AC-2 y AC-4), renombrar, cerrar y reabrir desde la cola (AC-5), y `transcript.txt` con `[hh:mm:ss] Nombre:` (AC-6). Y la revisión de las capturas con hablantes, con `image-reader`, para el contraste de la paleta (AC-4).
- **Por qué no se hizo**: pyannote está `missing` en este equipo (`studio engines list`). Su modelo es de acceso restringido en Hugging Face: pide un token y aceptar su licencia, y eso solo lo tiene el usuario.
- **Cuándo**: antes de publicar en `main`, o cuando el usuario instale pyannote desde Motores con su token.
- **Quién**: el usuario (token e instalación) y el agente (la corrida y la revisión).
- **Qué la cierra**: la transcripción desde la app de un clip de dos personas con «Identificar hablantes», y el `transcript.txt` revisado. Lo ya cubierto: las tres pruebas e2e de `tests/e2e/transcription/` (API grabada) y `app-check transcription` (sin hablantes), y AC-3 (motor ausente) en la app real.
