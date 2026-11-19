# 006: sección Narración

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `006-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en `out/narration/spec-006/` o en `tmp/spec-006/`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 20 archivos entre server y client) |
| Rama | `feature/006-narration-section` desde `origin/dev`, en `../content-studio-worktrees/006-narration-section/` |
| Depende de | 005 (fusionada en `origin/dev`; su carpeta se borró al cerrarla) |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Narrar desde el estudio. El guion se escribe en un editor que avisa en vivo de lo que rompe las reglas de `formato-guion.md`. Se eligen motor, voz, estilo e idioma (con ★ y memoria), y el resultado se escucha con su forma de onda y sus LUFS. También se puede ver la evaluación de whisper por párrafo, regenerar un solo párrafo y comparar tomas para elegir la mejor.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Server: linter del guion, información y picos del audio, y bloques persistidos | IMP |
| 2 | Server: trabajo `narration.regenerate` y tomas | IMP |
| 3 | Client: editor, opciones y generar | PEN |
| 4 | Client: reproductor con onda, evaluación, regenerar y comparar | PEN |

## Decisiones clave

* D-1: el linter del guion vive en el server (`narration/script_lint.py`) y la UI solo pinta sus avisos.
* D-2: el trabajo guarda `blocks/<i>.wav` y `script.json` en su carpeta, y `narration.regenerate` es un trabajo nuevo que rehace un bloque y escribe una toma nueva.
* D-3: `media/info` (duración y LUFS) y `media/peaks` en el server. La onda se dibuja con wavesurfer.js, que reusan la 010 y la 011.
* D-4: las tomas se agrupan por `script_hash`, y la elegida se marca con `jobs.starred` (migración 2).

## WARNING y PENDING

* WARNING: `006-wavesurfer.md` (dependencia nueva), `006-bloques-en-disco.md` (lo que ocupa), `006-soundfile-dev.md`, `006-narration-sin-torch.md`, `006-migracion-3.md`, `006-regenerar-sin-estado.md` y `006-tomas-y-grupo.md`.
* PENDING: `006-cli-carpeta-compartida.md`.
