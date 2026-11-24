---
modulo: installer
actualizada: 2026-11-24
---

# Instalador y actualizaciones

## Qué resuelve

Instalar Content Studio en Windows sin un checkout ni permisos de administrador, prepararlo solo en el primer arranque y actualizarlo desde GitHub Releases sin perder los datos del usuario.

## Qué hace hoy

- Instalador NSIS por usuario y en español, con `uv.exe` (versión fijada y verificada), el server versionado con su `uv.lock` y los datos que se siembran.
- Primer arranque: Tauri detecta el modo instalado, crea Python y el venv con `uv sync --frozen` en `%LOCALAPPDATA%\Content Studio\` y muestra la pantalla de preparación con reintento.
- `studio seed` copia los datos de la app sin pisar los que el usuario cambió; antes de migrar al actualizar, la base se respalda (5 últimos) y se restaura si la migración falla.
- Updater firmado: al abrir busca una versión nueva; «Actualizar y reiniciar» espera a que no haya trabajos corriendo. Ajustes > Acerca de muestra la versión y busca a pedido.
- Al desinstalar, los datos quedan salvo con la casilla «Borrar los datos de la aplicación» y una confirmación.
- `python -m devtools version|bundle|release` y `.github/workflows/release.yml` en tags `v*` (con `dry-run`).

## Dónde vive

- Tauri: `client/src-tauri/src/bootstrap*`, `lib.rs`, `tauri.conf.json`, `tauri.bundle.json` e `installer/nsis/hooks.nsh`.
- Cliente: `client/src/bootstrap/`, `shared/update/` y `features/settings/AboutSettings.tsx`.
- Server: `server/src/content_studio/seed.py`, el modo instalado en `paths.py` y el respaldo en `db/`.
- Devtools: `devtools/version.py`, `bundle.py` y `release.py`. Publicar: [release.md](../../operations/release.md).
- Decisiones: [022-datos-al-desinstalar](../WARNING/022-datos-al-desinstalar.md), [022-recursos-del-bundle](../WARNING/022-recursos-del-bundle.md) y [022-updater](../WARNING/022-updater.md); pendiente [022-firma-de-codigo](../PENDING/022-firma-de-codigo.md).

## Historial

- 2026-11-24: spec 022.
