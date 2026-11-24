# Spec 035, fase 1: archivos

## server/src/content_studio/diarization/

### Crear

- `diarization/__init__.py`, `assign.py`, `blocks.py`, `exports.py` y `speakers.py` (paleta y nombres), todos en stdlib.
- `server/tests/unit/src/content_studio/diarization/test_assign.py`, `test_blocks.py`, `test_exports.py` y `test_speakers.py`.
  - Verify: `uv run pytest server/tests/unit/src/content_studio/diarization -q`

### Solo lectura

- `docs/research/diarizacion-pyannote/04-integracion-con-faster-whisper.md` — algoritmo propuesto.
- `server/src/content_studio/transcription/transcribe_main.py` (`words_payload`) — formato de entrada.
