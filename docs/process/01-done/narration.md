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
- `uv run studio narration regenerate <job> <index>`: toma nueva con un párrafo rehecho; los demás bloques se copian byte a byte.
- Evaluación con whisper contra el guion (`--evaluate`): por párrafo, lo que oyó distinto, los silencios y los ritmos.
- Sección **Narración** de la app: editor con avisos en vivo (las reglas del guion que se comprueban sin modelo), importación de `.txt` y `.json`, opciones con ★ y licencia por motor, Generar con Ctrl+Enter. El resultado tiene onda, LUFS y pico; «Regenerar» rehace un párrafo; «Comparar» pone en columnas las tomas del texto y elige una con ★.
- Voces de referencia propias: se graban desde la app, en Mis voces (spec 010). El CLI `grabar`, legacy, se retiró en la 010.

## Dónde vive

- Código: `server/src/content_studio/narration/` (motores en `engines/` con `registry.py`; el linter en `script_lint.py`; las tomas en `takes.py`). Trabajos: `services/narration.py` y `services/narration_regenerate.py`. API: `api/routes/narration.py` y `media.py`.
- Cliente: `client/src/features/narration/` y `client/src/shared/media/`.
- Datos: `server/data/narration/` (README, docs, voces, venvs, motores). Uso y rendimiento: [server/data/narration/README.md](../../../server/data/narration/README.md).

## Límites conocidos

- La toma regenerada no se evalúa con whisper: Comparar la muestra como «Sin evaluar» ([WARNING 006-regenerar-sin-evaluacion](../WARNING/006-regenerar-sin-evaluacion.md)). Pendiente: [PENDING 006-evaluar-toma-regenerada](../PENDING/006-evaluar-toma-regenerada.md).
- El modo archivo de la CLI (`--output archivo.wav`) comparte `blocks/` entre tomas de una misma carpeta: [PENDING 006-cli-carpeta-compartida](../PENDING/006-cli-carpeta-compartida.md).

## Historial

- 2026-11-18: ficha inicial al adoptar `docs/process/`.
- 2026-11-19: CLI `studio` (004): `python cli.py narration tts` pasa a `uv run studio narration tts`; la salida va a `out/narration/<fecha>-<id>-<slug>/`. `grabar` se retiró en la 010.
- 2026-11-19: spec 006: la sección Narración, el linter, las tomas en disco con `blocks/`, regenerar un párrafo y comparar tomas.
