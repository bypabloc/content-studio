---
modulo: narration
actualizada: 2026-11-24
---

# Narración

## Qué resuelve

Voz en off para videos, en español neutro latinoamericano, clonando una voz de referencia con permiso de su dueño, en local (RTX 4060 de 8 GB).

## Qué hace hoy

- `uv run studio narration tts`: texto o guion → WAV en `out/narration/<AAAA-MM-DD>-<id>-<slug>/`, con estilo (12 estilos), motor y voz. Sin menú ni asistente: todos los flags van en la línea de comando. El comando encola el trabajo y lo corre en su proceso; `studio serve` corre los de la cola.
- Motores: VoxCPM2, Qwen3-TTS (0.6B y 1.7B), Chatterbox, CosyVoice 3, OmniVoice e IndexTTS, cada uno en su venv (licencias en `AGENTS.md`).
- `uv run studio narration voices`: catálogo de voces libres (CC0 o dominio público) que se construyen con `--build`.
- `uv run studio narration regenerate <job> <index>`: toma nueva con un párrafo rehecho; los demás bloques se copian byte a byte.
- Evaluación con faster-whisper contra el guion (`--evaluate`), con el modelo de Ajustes (large-v3-turbo por defecto): por párrafo, lo que oyó distinto, los silencios y los ritmos.
- Sección **Narración** de la app: editor con avisos en vivo (las reglas del guion que se comprueban sin modelo), importación de `.txt` y `.json`, opciones con ★ y licencia por motor, Generar con Ctrl+Enter. El resultado tiene onda, LUFS y pico; «Regenerar» rehace un párrafo; «Comparar» pone en columnas las tomas del texto y elige una con ★.
- Voces de referencia propias: se graban desde la app, en Mis voces (spec 010). El CLI `grabar`, legacy, se retiró en la 010.

## Dónde vive

- Código: `server/src/content_studio/narration/` (motores en `engines/` con `registry.py`; el linter en `script_lint.py`; las tomas en `takes.py`). Trabajos: `services/narration.py` y `services/narration_regenerate.py`. API: `api/routes/narration.py` y `media.py`.
- Cliente: `client/src/features/narration/` y `client/src/shared/media/`.
- Datos: `server/data/narration/` (README, docs, voces, venvs, motores). Uso y rendimiento: [server/data/narration/README.md](../../../server/data/narration/README.md).

## Límites conocidos

- La toma regenerada no se evalúa con whisper: Comparar la muestra como «Sin evaluar».
- El modo archivo de la CLI (`--output archivo.wav`) comparte `blocks/` entre tomas de una misma carpeta; `studio` no acepta `--output`, así que solo afecta a `python -m content_studio.narration.tts`.

## Versiones de los motores (spec 026, 2026-11-25)

Python y torch por motor, con su salida corta de verificación (duración, LUFS integrado y pico). Cada motor se instala en la Python más alta con la que instala y genera (D-1).

| Motor | Python | torch | Salida corta (verificada) | Nota |
| :--- | :---: | :--- | :--- | :--- |
| voxcpm2 | 3.14 | 2.11.0+cu128 | 2,06 s, -16,0 LUFS, pico -3,0 dBFS | 3.15: `pyahocorasick` sin rueda cp315 |
| qwen-0.6b | 3.14 | 2.11.0+cu128 | 1,78 s, -15,9 LUFS, pico -1,7 dBFS | 3.15: `onnxruntime` sin rueda cp315 |
| qwen-1.7b | 3.14 | 2.11.0+cu128 | 1,92 s, -15,9 LUFS, pico -1,9 dBFS | Igual que qwen-0.6b |
| chatterbox | 3.15 | 2.14.1+cu130 | 1,98 s, -16,6 LUFS, pico -1,5 dBFS | El mastering avisa -16,6 frente a -16,0 (ficha PENDING) |
| cosyvoice3 | 3.11 | 2.11.0+cu128 | 1,94 s, -16,4 LUFS, pico -1,5 dBFS | `pyworld` y `grpcio` pinados sin rueda cp312; `onnxruntime` 1.23.2 |
| omnivoice | 3.14 | 2.11.0+cu128 | Sin verificar | Falta aceptar la licencia CC-BY-NC (la aceptación es del usuario) |
| indextts | 3.11 | 2.8.0+cu128 | Sin verificar | Techo 3.11 del upstream; licencia bilibili pendiente |


## Historial

- 2026-11-24: «Revisar con IA» propone cambios por párrafo con el asistente local (spec 021).
- 2026-11-21: spec 013 (limpiador y faster-whisper): `--evaluate` y el chequeo de tomas usan el servicio de faster-whisper, no el comando `whisper` (AC-10).
- 2026-11-18: ficha inicial al adoptar `docs/process/`.
- 2026-11-20: spec 010 (voces y grabación): perfiles de voz con tomas y referencia elegida, grabación guiada con prueba de sala y chequeo, importar tramos de audio o video y favoritas en el catálogo (PR #80).
- 2026-11-19: CLI `studio` (004): `python cli.py narration tts` pasa a `uv run studio narration tts`; la salida va a `out/narration/<fecha>-<id>-<slug>/`. `grabar` se retiró en la 010.
- 2026-11-19: spec 006: la sección Narración, el linter, las tomas en disco con `blocks/`, regenerar un párrafo y comparar tomas.
