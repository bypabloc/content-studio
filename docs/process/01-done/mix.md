---
modulo: mix
actualizada: 2026-11-22
---

# Mezcla

## Qué resuelve

Pone la música bajo la voz con ducking y normaliza el resultado a un LUFS final. Opcionalmente suma la mezcla a un video, reemplazando su audio o por debajo de él.

## Qué hace hoy

- `uv run studio mix --voice <wav> --music <wav> [--mode transcript|sidechain] [--video <mp4> --video-mode replace|under]`. La voz la transcribe `studio clean` antes de sacar las rampas. Un trabajo por mezcla en `out/mix/<AAAA-MM-DD>-<id>-mix-render/`, con `mix.wav` (o `mix.mp4`), `params.json`, `duck.cmd` y `result.json` (medidas antes y después).
- Ducking por transcripción (-12 dB, rampas de 300 ms) o con `sidechaincompress`. Intro y outro; la música se corta a la duración de la voz; LUFS final -14 por defecto.
- Sección Mezcla en la app: línea de tiempo con regiones y rampas, vista previa en WebAudio, y «Mandar a Mezclar» desde Narración y Música (sin probar con la app real: ver pendientes).
- Salida a 48 kHz. El techo de pico es -1 dBTP para WAV y -2 dBTP para salidas con pérdida.

## Dónde vive

- Código: `server/src/content_studio/mix/` (`render.py`, `envelope.py`, `project.py`, `render_main.py`), `services/mix_render.py`, `api/routes/mix.py` y `cli/mix.py`. La sonoridad usa `media/normalize.py` (015).
- Cliente: `client/src/features/mix/`.
- Pruebas: unitarias en `server/tests/unit/src/content_studio/mix/` y `services/test_mix_render.py`; e2e en `tests/e2e/mix/`.
- Decisiones (historial de git de `docs/process/WARNING/`): 016-valores-ducking.
- Pendiente: la decisión sobre el LUFS de las mezclas con picos, en [PENDING/lufs-de-la-mezcla](../PENDING/lufs-de-la-mezcla.md).

## Historial

- 2026-11-22: spec 016 (T1 a T7): envolvente, render con ducking, video, CLI, API, cliente y e2e; salida a 48 kHz.

## Verificación (2026-11-22)

- Corridas reales (jobs 7 a 10): `transcript` y `sidechain` a 48 kHz, 30,510 s, -14,7 y -14,8 LUFS, pico -1,0 dBTP. Video `replace` y `under`: el stream de video es idéntico al original (md5) y el audio dura 30,528 s frente a los 30,520 s del video.
- Fuera de AC-3 en mezclas con picos (-14,7, -14,8 y -15,6 LUFS): pendiente.
- Pruebas: `mix` y `media` en verde (106); validadores en verde.
