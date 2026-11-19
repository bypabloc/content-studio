---
modulo: servidor
actualizada: 2026-11-19
---

# Servidor y CLI `studio`

## Qué resuelve

Genera narración y música sin abrir la interfaz: una API local y una cola de trabajos que comparten la app y el CLI `studio`, con los mismos servicios.

## Qué hace hoy

- API en `127.0.0.1` con token Bearer: catálogo, ajustes, trabajos, archivos y progreso por SSE (`/events`).
- Cola en SQLite (`var/content-studio.db`) con un worker que toma la GPU con el candado de `gpu_lock.py`. Permite encolar, cancelar, reintentar, reordenar y pausar.
- Cancelar termina el proceso del trabajo y sus hijos (`taskkill /T /F` en Windows; SIGTERM al grupo y SIGKILL a los 5 s en POSIX).
- CLI: `studio serve`, `narration tts`, `narration voices`, `music` y `jobs list|cancel|retry`. Sin menú ni asistente.
- Salida: `out/<herramienta>/<AAAA-MM-DD>-<id>-<slug>/` con `params.json`; log en `logs/jobs/<id>.log`.

## Dónde vive

- Código: `server/src/content_studio/{api,db,jobs,services,cli}/`, `gpu_lock.py` y `messages/es.json`.
- Un tipo de trabajo nuevo es un módulo en `services/` y una línea en `SERVICES` (`services/registry.py`).

## Historial

- 2026-11-19: ficha inicial con la spec 004 (cola, API, SSE y CLI `studio`; se borran `cli.py` y el asistente).
