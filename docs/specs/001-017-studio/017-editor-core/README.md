# 017: Editor (núcleo): proyecto, línea de tiempo multipista, explorador, grabar y exportar audio

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `017-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. **El editor es no destructivo: nunca modifica, mueve ni borra un archivo de entrada**; solo escribe dentro de la carpeta de su proyecto. El explorador solo lee carpetas. Las pruebas usan medios generados en `tmp/spec-017/`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 30 archivos entre server y client) |
| Rama | `feature/017-editor-core` desde `origin/dev`, en `../content-studio-worktrees/017-editor-core/` |
| Depende de | [016](../016-mix-ducking/README.md) (fusionada en `origin/dev`); usa la grabación de la 010 y `media/edit.py` y `normalize.py` de la [015](../015-convert-normalize-trim/README.md) |
| Origen | Pedido del usuario (2026-11-19), lote [001-017-studio](../README.md). Primera de tres: 017 núcleo y audio, [018](../018-editor-visual/README.md) video e imágenes, [019](../019-editor-effects/README.md) texto, efectos y «Mandar a» |

## Objetivo

Una sección **Editor** (un NLE no destructivo) donde se crea un proyecto, se traen medios importando, grabando con el micrófono o navegando las carpetas del sistema, y se arman en una línea de tiempo con pistas ilimitadas: mover, cortar, superponer, unir, fades y volumen por clip, con imán, marcadores y deshacer. Esta spec deja el editor completo para audio y lo exporta (con normalización opcional); las pistas visuales llegan en la 018.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Modelo del proyecto (puro, versionado) y fixtures compartidas server/client | DON |
| 2 | Proyectos en disco y API; explorador de carpetas | DON |
| 3 | Render de audio con `filter_complex` y exportación con normalizar | DON |
| 4 | Client: estado, historial (deshacer y rehacer) y operaciones de edición | DON |
| 5 | Client: línea de tiempo, imán, marcadores, transporte y vista previa | DON |
| 6 | Client: explorador, importar, soltar desde Windows y grabar | DON |

## Decisiones clave

* D-1: el proyecto es un `project.json` versionado en su carpeta; SQLite no gana tablas (los recientes van en `settings`).
* D-2: el modelo y su matemática de tiempos se definen una vez en Python y se espejan en TypeScript, atados por fixtures JSON compartidas que prueban los dos lados.
* D-3: exportar es un trabajo `editor.render` que arma un `filter_complex` (en archivo, no en la línea de comandos) y recodifica con la 015.
* D-4: vista previa de audio con elementos `<audio>` por clip y WebAudio (`GainNode`), sin decodificar archivos enteros en memoria.
* D-5: explorador propio sobre `GET /fs/*` (solo lectura) + diálogo nativo + soltar desde el Explorador de Windows.

## WARNING y PENDING

* WARNING: `017-proyecto-json.md`, `017-latencia-grabacion.md`, `017-preview-media-elements.md` y `017-presupuesto-js.md`.
* PENDING: `017-app-check-y-flujo-real.md`, `017-e2e-runner.md` y `017-pytest-temp.md`; el CLI y los cuatro e2e del Editor pasan.
