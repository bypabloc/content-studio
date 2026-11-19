# 015: Editor (núcleo): proyecto, línea de tiempo multipista, explorador, grabar y exportar audio

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `015-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. **El editor es no destructivo: nunca modifica, mueve ni borra un archivo de entrada**; solo escribe dentro de la carpeta de su proyecto. El explorador solo lee carpetas. Las pruebas usan medios generados en `tmp/spec-015/`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 30 archivos entre server y client) |
| Rama | `feature/015-editor-core` desde `origin/dev`, en `../content-studio-worktrees/015-editor-core/` |
| Depende de | [014](../014-mix-ducking/README.md) (fusionada en `origin/dev`); usa la grabación de la [008](../008-voices-recording/README.md) y `media/edit.py` y `normalize.py` de la [013](../013-convert-normalize-trim/README.md) |
| Origen | Pedido del usuario (2026-11-19), lote [001-017-studio](../README.md). Primera de tres: 015 núcleo y audio, [016](../016-editor-visual/README.md) video e imágenes, [017](../017-editor-effects/README.md) texto, efectos y «Mandar a» |

## Objetivo

Una sección **Editor** (un NLE no destructivo) donde se crea un proyecto, se traen medios importando, grabando con el micrófono o navegando las carpetas del sistema, y se arman en una línea de tiempo con pistas ilimitadas: mover, cortar, superponer, unir, fades y volumen por clip, con imán, marcadores y deshacer. Esta spec deja el editor completo para audio y lo exporta (con normalización opcional); las pistas visuales llegan en la 016.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Modelo del proyecto (puro, versionado) y fixtures compartidas server/client | PEN |
| 2 | Proyectos en disco y API; explorador de carpetas | PEN |
| 3 | Render de audio con `filter_complex` y exportación con normalizar | PEN |
| 4 | Client: estado, historial (deshacer y rehacer) y operaciones de edición | PEN |
| 5 | Client: línea de tiempo, imán, marcadores, transporte y vista previa | PEN |
| 6 | Client: explorador, importar, soltar desde Windows y grabar | PEN |

## Decisiones clave

* D-1: el proyecto es un `project.json` versionado en su carpeta; SQLite no gana tablas (los recientes van en `settings`).
* D-2: el modelo y su matemática de tiempos se definen una vez en Python y se espejan en TypeScript, atados por fixtures JSON compartidas que prueban los dos lados.
* D-3: exportar es un trabajo `editor.render` que arma un `filter_complex` (en archivo, no en la línea de comandos) y recodifica con la 013.
* D-4: vista previa de audio con elementos `<audio>` por clip y WebAudio (`GainNode`), sin decodificar archivos enteros en memoria.
* D-5: explorador propio sobre `GET /fs/*` (solo lectura) + diálogo nativo + soltar desde el Explorador de Windows.

## WARNING y PENDING

* WARNING: `015-proyecto-json.md` (esquema v1 y migraciones de versión), `015-latencia-grabacion.md` (compensación al grabar sobre lo que suena) y `015-preview-media-elements.md` (por qué no `decodeAudioData`).
* PENDING: ninguna.
