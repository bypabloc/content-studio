# 012: Motores (instalar bajo demanda), almacenamiento elegible, ffmpeg del sistema y bienvenida

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `012-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Los motores instalados a mano en modo dev se marcan como **externos** y nunca se desinstalan ni se mueven sin confirmación explícita. Las pruebas de instalación usan una carpeta de datos temporal (`tmp/spec-012/data/`). Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 25 archivos entre server y client) |
| Rama | `feature/012-engines-storage` desde `origin/dev`, en `../content-studio-worktrees/012-engines-storage/` |
| Depende de | [011](../011-music-section/README.md) (fusionada en `origin/dev`) y [002](../002-english-cspell/README.md) (renombra las rutas que esta spec usa) |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Que el estudio pueda instalar, verificar, reparar y desinstalar cada motor desde la UI, con su licencia, tamaño, requisitos de GPU y progreso. También detecta ffmpeg (y git) y los instala con winget si faltan, deja elegir dónde viven los modelos y las salidas, y guía el primer uso con un asistente de bienvenida. Por defecto, venvs y pesos viven fuera del checkout, en una carpeta que el usuario puede cambiar: el checkout solo guarda código y datos versionados.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Rutas dinámicas: carpeta de datos y almacenamiento, con la reubicación en el server | DON |
| 2 | Herramientas del sistema: ffmpeg, git y GPU (detectar e instalar) | DON |
| 3 | Recetas y ejecutor: instalar, verificar, reparar y desinstalar como trabajos | IMP |
| 4 | Client: Motores, Ajustes > Almacenamiento y bienvenida | PEN |

## Decisiones clave

* D-1: `paths` pasa a funciones que leen `storage.*` de `settings`. El valor por defecto es una carpeta fuera del checkout, también en dev (`%LOCALAPPDATA%\Content Studio\` o `~/.local/share/content-studio/`); el checkout solo guarda código y datos versionados.
* D-2: recetas como datos (`engines/recipes/<engine>.json`) con pasos idempotentes: `python`, `venv`, `pip`, `git`, `hf` y `post`.
* D-3: el instalador es un trabajo `engine.install` (recurso `cpu`; la descarga no usa GPU) con `@@progress` por paso y por bytes.
* D-4: `HF_HOME` apunta a la carpeta de modelos, para que desinstalar sepa qué borrar. Cada instalación deja un `install.json` (dueño `app` o `external`).
* D-5: ffmpeg y git del PATH. Si faltan, se instalan con `winget --scope user` y se avisa. Si no se puede, se muestran instrucciones.
* D-6: la reubicación de carpetas (mover y reescribir `.pth` y `direct_url.json`) se mueve de `devtools/move_data.py` a `content_studio/storage/relocate.py`.

## WARNING y PENDING

* WARNING: `012-recetas.md` (versiones fijadas y commits de los repos), `012-winget.md`, `012-mover-entre-discos.md`, `012-desinstalacion-externa.md` y `012-error-disk-full.md`.
* PENDING: ninguna.
