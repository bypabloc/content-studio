---
modulo: servidor
actualizada: 2026-11-25
---

# Servidor y CLI `studio`

## Qué resuelve

Genera narración y música sin abrir la interfaz: una API local y una cola de trabajos que comparten la app y el CLI `studio`, con los mismos servicios.

## Qué hace hoy

- API en `127.0.0.1` con token Bearer: catálogo, ajustes, trabajos, archivos y progreso por SSE (`/events`).
- Cola en SQLite (`var/content-studio.db`) con un worker que toma la GPU con el candado de `gpu_lock.py`. Permite encolar, cancelar, reintentar, reordenar y pausar.
- Cancelar termina el proceso del trabajo y sus hijos (`taskkill /T /F` en Windows; SIGTERM al grupo y SIGKILL a los 5 s en POSIX).
- Al arrancar, el server interrumpe solo los trabajos cuyo proceso murió (`owner_pid`); lo que la CLI tiene en curso sigue.
- CLI: `studio serve`, `narration tts`, `narration voices`, `music` y `jobs list|cancel|retry`. Sin menú ni asistente.
- Servidor compartido (spec 028): `studio api up|status|down|token`. Una sola instancia por instalación, en `127.0.0.1:41830` (configurable; si está ocupado, otro puerto). `api up` arranca el server o reutiliza el que responde (y con `--with-token` da el token a la ventana). `api down` se niega con trabajos activos, salvo `--force`. Apagado por inactividad (`api.idle_minutes`, 10 por defecto), aunque la ventana esté abierta; `api up` lo vuelve a levantar. El token persiste en `api-token`; `api token --rotate` lo cambia.
- Guarda de Host: solo `127.0.0.1` o `localhost` con el puerto del server; si no, 400 `error.host_not_allowed`.
- Red local (spec 032): con `api.lan.enabled`, `serve` levanta un segundo listener con TLS en `api.lan.address:api.lan.port` (41831), con una lista cerrada de rutas y el token de cada dispositivo; `PUT /lan/settings` lo enciende o apaga sin reiniciar. Migración 10: `api_clients`, `uploads` y `jobs.client_id`. Ficha: [integrations.md](integrations.md).
- Salida: `out/<herramienta>/<AAAA-MM-DD>-<id>-<slug>/` con `params.json`; log en `logs/jobs/<id>.log`.
- Idioma de la API: responde en el idioma de `Accept-Language` (`es`, `en` o `pt`; si no coincide, `es`). Cada error lleva `code`, `params` y el `message` ya traducido; un error sin texto propio usa `error.http.<status>`.
- MCP (spec 029): `studio mcp` habla MCP por stdio con diez herramientas `studio_*`, sin las administrativas; `studio mcp config --client <c>` imprime la configuración de cada cliente. Ficha: [integrations.md](integrations.md).

## Dónde vive

- Código: `server/src/content_studio/{api,db,jobs,services,cli}/`, `runtime/` (descubrimiento, instancia única e inactividad), `gpu_lock.py` y `messages.py`.
- Textos: `server/src/content_studio/messages/{es,en,pt}.json`; el idioma de la petición se negocia en `messages.negotiate`.
- Un tipo de trabajo nuevo es un módulo en `services/` y una línea en `SERVICES` (`services/registry.py`).
- MCP: `server/src/content_studio/mcp_server/` (catálogo, herramientas, puente, SDK y `config.py`) y `cli/mcp.py`.

## Historial

- 2026-11-19: ficha inicial con la spec 004 (cola, API, SSE y CLI `studio`; se borran `cli.py` y el asistente).
- 2026-11-19: spec 007 (i18n): la API responde en el idioma de `Accept-Language`; el catálogo pasa a `messages/{es,en,pt}.json`.
- 2026-11-24: spec 025: el server corre en Python 3.15 (`.python-version`); el piso de los motores (hoy 3.10) sale de sus recetas.
- 2026-11-25: spec 029 (MCP): `studio mcp` y `studio mcp config`; `GET /integrations/mcp-config` para Ajustes.
- 2026-11-25: spec 032 (red local): segundo listener opt-in, dispositivos con token y subidas.
- 2026-11-25: spec 028 (server compartido): `studio api` y una sola instancia; la ventana se adjunta y no lo posee.
