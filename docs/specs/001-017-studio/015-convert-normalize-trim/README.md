# 015: Convertir (formatos, redes, GIF y extraer audio), Normalizar y operaciones de recorte y unión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `015-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. **Ninguna herramienta modifica sus archivos de entrada**: todas escriben uno nuevo. Las pruebas usan medios generados en `tmp/spec-015/`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 30 archivos entre server y client) |
| Rama | `feature/015-convert-normalize-trim` desde `origin/dev`, en `../content-studio-worktrees/015-convert-normalize-trim/` |
| Depende de | [014](../014-subtitles/README.md) (por `common/encode.py`), fusionada en `origin/dev` |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Las herramientas de ffmpeg del estudio, cada una con su lote, su cola y su vista:

* **Convertir**: audio y video a los formatos estándar con calidad, canales, frecuencia y resolución; presets de redes con encuadre centrado, manual, con barras o fondo desenfocado, o siguiendo a la persona; GIF; y extraer audio.
* **Normalizar**: LUFS por presets en dos pasadas, con medición de antes y después, A/B y «mejorar voz» opcional.
* **Recortar, unir y dividir** (solo server, API y cola): un tramo, unir con crossfade, fades y dividir en partes. La pantalla de edición es el Editor de las [017–019](../017-editor-core/README.md), que usa estas operaciones; esta spec no crea `features/edit/`.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Catálogo de formatos y presets, y el armador de comandos de conversión (T1–T2) | DON |
| 2 | Encuadre: centrado, manual, barras o desenfoque, y seguir a la persona (YuNet) (T3–T4) | DON |
| 3 | Normalizar (loudnorm en dos pasadas y mejorar voz) (T5) | DON |
| 4 | Recortar, unir, fades y dividir (T6) | DON |
| 5 | Client: Convertir y Normalizar (T7), con la CLI y el e2e de T8 | DON |

## Decisiones clave

* D-1: `media/convert.py` arma los comandos de ffmpeg a partir de un catálogo de datos (`media/formats.py` y `media/presets.py`), sin una clase por formato.
* D-2: los trabajos de ffmpeg son `cpu` y van en paralelo con el pool de la 004.
* D-3: seguir a la persona con YuNet (OpenCV) en `.venv-vision` (receta de la 012), con la trayectoria suavizada y aplicada con `sendcmd` sobre `crop`.
* D-4: normalizar con `loudnorm` en dos pasadas (medir y aplicar `linear=true`), con true peak ≤ -1 dBTP.
* D-5: recortar y unir con `trim`/`atrim` + `concat`/`xfade`/`acrossfade`, recodificando con `common/encode.py`.

## WARNING y PENDING

* WARNING: `015-seguir-a-la-persona.md` (YuNet: modelo y licencia), `015-normalizar.md` (cadena de «mejorar voz» y techo de pico con pérdida) y `015-verificacion-final.md` (corridas reales), más las fichas de cada tarea.
* PENDING: `015-escucha-y-revision.md` (lo que escucha y mira el usuario), `015-trayectoria-y-ab-fuera-de-out.md`, `015-foto-de-prueba.md`, `015-bitrates-presets.md`, `015-refactor-masterizacion-narracion.md` y `015-repair-primera-instalacion.md`.
