# Spec 035, fase 2: archivos

### Crear

- `server/src/content_studio/diarization/diarize_main.py` — pyannote en `.venv-diarize`.
- `server/src/content_studio/diarization/speaker_audio.py` — comandos de ffmpeg.
- `server/tests/unit/src/content_studio/diarization/test_diarize_main.py` y `test_speaker_audio.py`.
  - Verify: `uv run pytest server/tests/unit/src/content_studio/diarization -q`

### Modificar

- `server/src/content_studio/engines/verification.py` — rama `diarization`.
- `server/tests/unit/src/content_studio/engines/test_verification.py`.
  - Verify: `uv run pytest server/tests/unit/src/content_studio/engines -q`

### Solo lectura

- `server/src/content_studio/common/process.py` (`use_venv`) y `common/progress.py`.
- `server/src/content_studio/transcription/transcribe_main.py` — patrón de relanzamiento y extracción a 16 kHz.
