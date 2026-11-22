# 014: Subtítulos (SRT/VTT, editor, quemado y estilo de redes)

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `014-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Quemar subtítulos nunca modifica el video de entrada. Las pruebas usan medios generados en `tmp/spec-014/`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 25 archivos entre server y client, más las fuentes OFL) |
| Rama | `feature/014-subtitles` desde `origin/dev`, en `../content-studio-worktrees/014-subtitles/` |
| Depende de | [013](../013-whisper-cleaner/README.md) (fusionada en `origin/dev`) |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Crear subtítulos a partir de cuatro fuentes: un archivo transcrito con faster-whisper, el resultado del Limpiador, una narración (alineada con el texto exacto del guion) o un SRT/VTT importado. Se editan (texto, tiempos, dividir, unir y palabras clave) con una vista previa exacta sobre el video y las zonas seguras de redes, se les da estilo con presets incluidos o propios, y se exportan a SRT, VTT o ASS. También se pueden quemar en el video, en estilo clásico o de redes con la palabra resaltada, y traducir la pista al inglés.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Documento de subtítulos, segmentación y formatos (SRT, VTT y ASS) | DON |
| 2 | Orígenes: transcribir, limpiador, narración (alineación) e importar | DON |
| 3 | Estilos, presets, fuentes y quemado | DON |
| 4 | Traducción al inglés | DON |
| 5 | Client: editor, vista previa JASSUB, zonas seguras y estilos, y «Subtitular» desde el limpiador y la narración (e2e) | DON |
| 6 | Corridas reales y verificación final (T9): parcial, ver `03-verificacion-final.md` §6 | PEN |

## Decisiones clave

* D-1: un documento `subtitles.json` en disco por proyecto (cues con palabras). La base solo guarda su ruta (tabla `subtitle_projects`).
* D-2: la segmentación es una función pura con límites configurables (caracteres, líneas, duración y palabras por subtítulo en el estilo de redes).
* D-3: ASS como formato de render. La vista previa usa JASSUB (libass en wasm) y el quemado `ffmpeg subtitles=` con `fontsdir`: el mismo motor en los dos lados.
* D-4: la alineación de una narración usa el texto del guion con los tiempos de las palabras de whisper (difflib).
* D-5: las fuentes OFL van versionadas en `server/data/fonts/` con sus licencias, y las del sistema se descubren en las carpetas de fuentes de Windows.

## WARNING y PENDING

* WARNING: fichas `014-*` en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (editor y preview, quemar, traducir, fuentes OFL, migración 5, orígenes, exportar y la corrección de la vista previa).
* PENDING: `014-audio-quemar-copia`, `014-traduccion-real`, `014-capturas-editor` y `014-escucha-y-revision` en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
