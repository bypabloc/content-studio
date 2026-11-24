---
modulo: voices
actualizada: 2026-11-24
---

# Voces y grabación

## Qué resuelve

Tener voces para narrar: perfiles propios grabados con el micrófono o importados de un audio o video con permiso, y un catálogo de voces libres que se construyen y aprueban por estilo.

## Qué hace hoy

- Mis voces: perfiles con una toma por estilo (los 12 del kit de grabación), elegida entre varias; el perfil por defecto es «Mi voz».
- Grabar en la app: elección de micrófono, prueba de sala, teleprompter con el texto marcado del kit y registro opcional del micrófono.
- Importar un tramo de 9 a 12 s de un audio o video (`/voices/profiles/<slug>/import`, con consentimiento) con la onda para elegirlo.
- Chequeo de cada toma (`voice.check`): duración del estilo, pico, silencio en los bordes, ruido de sala y pausas, con el motivo en el catálogo de textos.
- Catálogo de voces libres: fuentes con licencia, construcción por estilo (`voice.build`) y aprobación; `studio narration voices --build`.

## Dónde vive

- Server: `server/src/content_studio/narration/voices/` (catalog, sources, build), `narration/profiles.py`, `profile_takes.py`, `recording_kit.py`, `services/voice_check.py`, `services/voice_build.py` y `api/routes/voices*.py`.
- Cliente: `client/src/features/voices/` y `client/src/features/recording/`.
- Pruebas: `server/tests/unit/src/content_studio/narration/`, `client/tests/unit/src/features/{voices,recording}/` y `tests/e2e/voices/`.

## Historial

- 2026-11-20: spec 010 (voces y grabar).
- 2026-11-24: verificación integral (023): perfil importado en la app instalada; el chequeo marca «retake» en referencias ya masterizadas, sin silencio en los bordes.
