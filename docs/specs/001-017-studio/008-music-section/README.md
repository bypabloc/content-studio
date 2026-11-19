# 008: sección Música con duración exacta

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `008-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en `out/music/spec-008/` o en `tmp/spec-008/`, y las muestras en `server/data/music/samples/` (carpeta nueva). Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 18 archivos entre server y client) |
| Rama | `feature/008-music-section` desde `origin/dev`, en `../content-studio-worktrees/008-music-section/` |
| Depende de | 005 y [006](../006-narration-section/README.md) (Player y CompareTakes), fusionadas en `origin/dev` |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Generar música instrumental de la **duración exacta pedida**, en mm:ss o igualada a una narración o a un video. Los 126 presets se eligen en un buscador por categoría, con muestras de 10 s y favoritos, o se describe la música con texto libre guiado (tonalidad, BPM con tap tempo y compás). Las variantes se comparan y se elige una, con la medición de voz de demucs.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Server: duración exacta (margen, recorte, fade y regenerar si sale corta) | PEN |
| 2 | Server: categorías, catálogo de estilos y muestras de 10 s | PEN |
| 3 | Client: duración, buscador de estilos y texto libre guiado | PEN |
| 4 | Client: variantes con comparar y elegir | PEN |

## Decisiones clave

* D-1: la duración exacta se resuelve en `music_main.py`: pedido + 25 % (mínimo +10 s), recorte de silencio, corte exacto con fade-out de 2 s y hasta 2 regeneraciones.
* D-2: el campo `category` se agrega a cada preset en `styles.py`, que es la fuente.
* D-3: las muestras son un trabajo `music.samples` (ACE-Step con `--no-lm` y 10 s), reanudable, en `server/data/music/samples/`.
* D-4: `CompareTakes` pasa a `shared/components/`, y las variantes se agrupan con `group_key`.

## WARNING y PENDING

* WARNING: `008-duracion-exacta.md` (cuánto margen y por qué) y `008-muestras.md` (espacio y tiempo de GPU).
* PENDING: ninguna.
