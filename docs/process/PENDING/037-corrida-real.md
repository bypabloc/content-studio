# 037: corrida real de Hablantes (pyannote) y medición de los WAV por hablante

- **Qué**: la corrida real de «Identificar» con un clip de dos personas: que las regiones coincidan con lo que se oye en cinco turnos (AC-2), que el renombrado llegue a `turns.csv` (AC-3), que «Un audio por hablante» dé dos WAV que suenan bien y se midan (duración, LUFS y espectrograma en `tmp/spec-037/`, con `image-reader`) (AC-5), y que «Abrir en el Editor» abra el proyecto con sus marcadores (AC-6).
- **Por qué no se hizo**: `.venv-diarize` no está instalado en este equipo (`studio engines`). Su modelo `pyannote/speaker-diarization-community-1` es de acceso restringido en Hugging Face: pide un token y aceptar la licencia, y eso solo lo tiene el usuario.
- **Cuándo**: antes de publicar en `main`, o cuando el usuario instale pyannote desde Motores con su token.
- **Quién**: el usuario (token e instalación) y el agente (la corrida, la medición y la revisión de las imágenes).
- **Qué la cierra**: la identificación real de un clip de dos personas desde la sección Hablantes, con los puntos de arriba revisados y las rutas de los WAV en el reporte. Lo ya cubierto sin motor: las tres pruebas e2e de `tests/e2e/speakers/` (API grabada), `app-check speakers` (sección en claro y oscuro) y las pruebas unitarias de la API de diarización.
