---
modulo: narration
actualizada: 2026-11-18
---

# Narración

## Qué resuelve

Voz en off para videos, en español neutro latinoamericano, clonando una voz de referencia con permiso de su dueño, en local (RTX 4060 de 8 GB).

## Qué hace hoy

- `python cli.py narration tts`: texto o guion → WAV en `out/narration/`, con estilo (12 estilos), motor y voz; el asistente pide lo que falta.
- Motores: VoxCPM2, Qwen3-TTS (0.6B y 1.7B), Chatterbox, CosyVoice 3, OmniVoice e IndexTTS, cada uno en su venv (licencias en `AGENTS.md`).
- `narration voces`: catálogo de voces libres (CC0 o dominio público) que se construyen con `--construir`.
- `narration grabar`: kit para grabar las voces de referencia propias.
- Evaluación con whisper contra el guion (`narration/evaluacion/`: comparar y revisar).

## Dónde vive

- Código: `src/content_studio/narration/` (motores en `motores/` con `registro.py`).
- Datos: `narration/` (README, docs, voces, venvs, motores). Uso y rendimiento: [narration/README.md](../../../narration/README.md).

## Historial

- 2026-11-18: ficha inicial al adoptar `docs/process/`.
