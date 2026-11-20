# 022: instalador NSIS, primer arranque, actualizaciones y releases

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `022-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Las pruebas de instalación usan un usuario de Windows de prueba o carpetas temporales (`CONTENT_STUDIO_HOME`), nunca las carpetas reales del usuario. **Cargar la clave del updater como secret de GitHub requiere la aprobación del usuario** (`blocked — credentials` si no está). Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 15 archivos entre Rust, devtools, CI y docs) |
| Rama | `feature/022-installer` desde `origin/dev`, en `../content-studio-worktrees/022-installer/` |
| Depende de | [021](../021-local-llm-assist/README.md) (fusionada en `origin/dev`; se ejecuta después de la 020) |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Que Content Studio se instale en cualquier Windows con un instalador NSIS por usuario, sin permisos de administrador. Al abrirlo por primera vez, prepara su Python y el venv del server con uv mostrando el progreso, siembra los datos de la app sin pisar los del usuario y pasa a la bienvenida de la 012. Se actualiza solo desde GitHub Releases, y una release se publica con un tag `vX.Y.Z`.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Modo instalado: resolución de rutas, recursos empaquetados y siembra de datos | PEN |
| 2 | Primer arranque en Rust: uv python, uv sync y pantalla de progreso | PEN |
| 3 | NSIS: por usuario, en español, accesos y desinstalar conservando datos | PEN |
| 4 | Updater, versión y workflow de release | PEN |

## Decisiones clave

* D-1: el instalador trae `uv.exe`, el código del server (`server/src`, `pyproject.toml` y `uv.lock`) y los datos versionados como recursos de Tauri. Python y el venv se crean en el primer arranque.
* D-2: el primer arranque lo hace Rust (antes de que exista el server), con eventos de progreso a una pantalla de preparación.
* D-3: la siembra copia los datos versionados (catálogo, guiones, fuentes y recetas) solo si faltan o si su versión es más nueva, y nunca pisa los del usuario.
* D-4: `tauri-plugin-updater` contra `latest.json` del último Release, con la firma del updater.
* D-5: `release.yml` corre en tags `v*` sobre `windows-latest`, y `python -m devtools version <x.y.z>` sube la versión en todos los manifiestos.

## WARNING y PENDING

* WARNING: `022-recursos-empaquetados.md` y `022-smartscreen.md`.
* PENDING: `022-firma-de-codigo.md` (costo, decide el usuario).
