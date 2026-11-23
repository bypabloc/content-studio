# 019: Editor (efectos): texto y títulos, velocidad, color y LUT, chroma key, modos de fusión, subtítulos y «Mandar a»

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `019-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. El editor nunca modifica sus archivos de entrada; los textos rasterizados y los LUT importados van a la carpeta del proyecto. Las pruebas usan medios generados en `tmp/spec-019/`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 25 archivos entre server y client) |
| Rama | `feature/019-editor-effects` desde `origin/dev`, en `../content-studio-worktrees/019-editor-effects/` |
| Depende de | [018](../018-editor-visual/README.md) (fusionada en `origin/dev`); usa el ASS y JASSUB de la [014](../014-subtitles/README.md) |
| Origen | Pedido del usuario (2026-11-19), lote [001-017-studio](../README.md). Tercera de tres del Editor |

## Objetivo

Cerrar el Editor como NLE: clips de texto con estilo y animación, cambio de velocidad, corrección de color con LUT, chroma key (fondo verde), modos de fusión entre capas, los subtítulos de la 014 como pista y la integración con el resto del estudio: «Abrir en Editor» desde las secciones y «Mandar a…» desde la exportación.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Esquema v3 (texto, velocidad, efectos y fusión) y sus fixtures | PEN |
| 2 | Texto rasterizado en el client como imagen con alfa | PEN |
| 3 | Velocidad en audio y video | PEN |
| 4 | Color, LUT, chroma y fusión: filtros de ffmpeg y shaders con paridad | PEN |
| 5 | Pista de subtítulos (014) | PEN |
| 6 | «Abrir en Editor» y «Mandar a…» | PEN |

## Decisiones clave

* D-1: el texto se rasteriza una vez en el client a PNG con alfa y se usa como imagen en la vista previa y en la exportación: una sola implementación del dibujo.
* D-2: velocidad con `setpts` y `atempo` encadenado; la matemática de tiempos va a las fixtures compartidas.
* D-3: color con `eq` y `lut3d`, chroma con `chromakey`, y fusión con `blend` + `alphamerge`; cada uno con su shader y casos de paridad SSIM.
* D-4: los subtítulos son una pista que apunta a un proyecto de la 014 y se queman con su ASS; la vista previa usa JASSUB como en la 014.

## WARNING y PENDING

* WARNING: `019-texto-rasterizado.md` (por qué no `drawtext`), `019-control-velocidad.md` (control en el Inspector), `019-fusion-con-alfa.md` (cadena de filtros) y `019-chroma-paridad.md` (fórmula y umbral).
* PENDING: ninguna.
