---
modulo: narration
actualizada: 2026-11-19
---

# Narración

## Qué resuelve

Voz en off para videos, en español neutro latinoamericano, clonando una voz de referencia con permiso de su dueño, en local (RTX 4060 de 8 GB).

## Qué hace hoy

- `uv run studio narration tts`: texto o guion → WAV en `out/narration/<AAAA-MM-DD>-<id>-<slug>/`, con estilo (12 estilos), motor y voz. Sin menú ni asistente: todos los flags van en la línea de comando. El comando encola el trabajo y lo corre en su proceso; `studio serve` corre los de la cola.
- Motores: VoxCPM2, Qwen3-TTS (0.6B y 1.7B), Chatterbox, CosyVoice 3, OmniVoice e IndexTTS, cada uno en su venv (licencias en `AGENTS.md`).
- `uv run studio narration voices`: catálogo de voces libres (CC0 o dominio público) que se construyen con `--build`.
- `grabar`: kit para grabar las voces de referencia propias. Es legacy, fuera de `studio`: `uv run --group legacy python -m content_studio.narration.grabar.main`.
- Evaluación con whisper contra el guion (`server/data/narration/evaluation/`: comparar y revisar).

## Dónde vive

- Código: `server/src/content_studio/narration/` (motores en `engines/` con `registry.py`). El trabajo que encola `studio` está en `server/src/content_studio/services/narration.py`.
- Datos: `server/data/narration/` (README, docs, voces, venvs, motores). Uso y rendimiento: [server/data/narration/README.md](../../../server/data/narration/README.md).

## Historial

- 2026-11-18: ficha inicial al adoptar `docs/process/`.
- 2026-11-19: CLI `studio` (004): `python cli.py narration tts` pasa a `uv run studio narration tts`; la salida va a `out/narration/<fecha>-<id>-<slug>/`. `grabar` sigue en legacy.
