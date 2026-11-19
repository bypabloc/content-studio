# 012: Convertir (formatos, redes, GIF y extraer audio), Normalizar y Recortar y unir

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `012-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. **Ninguna herramienta modifica sus archivos de entrada**: todas escriben uno nuevo. Las pruebas usan medios generados en `tmp/spec-012/`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 30 archivos entre server y client) |
| Rama | `feature/012-convert-normalize-trim` desde `origin/dev`, en `../content-studio-worktrees/012-convert-normalize-trim/` |
| Depende de | [011](../011-subtitles/README.md) (por `common/encode.py`), fusionada en `origin/dev` |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Las herramientas de ffmpeg del estudio, cada una con su lote, su cola y su vista:

* **Convertir**: audio y video a los formatos estándar con calidad, canales, frecuencia y resolución; presets de redes con encuadre centrado, manual, con barras o fondo desenfocado, o siguiendo a la persona; GIF; y extraer audio.
* **Normalizar**: LUFS por presets en dos pasadas, con medición de antes y después, A/B y «mejorar voz» opcional.
* **Recortar y unir**: un tramo, unir con crossfade, fades y dividir en partes.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Catálogo de formatos y presets, y el armador de comandos de conversión | PEN |
| 2 | Encuadre: centrado, manual, barras o desenfoque, y seguir a la persona (YuNet) | PEN |
| 3 | Normalizar (loudnorm en dos pasadas y mejorar voz) | PEN |
| 4 | Recortar, unir, fades y dividir | PEN |
| 5 | Client: Convertir, Normalizar y Recortar y unir | PEN |

## Decisiones clave

* D-1: `media/convert.py` arma los comandos de ffmpeg a partir de un catálogo de datos (`media/formats.py` y `media/presets.py`), sin una clase por formato.
* D-2: los trabajos de ffmpeg son `cpu` y van en paralelo con el pool de la 004.
* D-3: seguir a la persona con YuNet (OpenCV) en `.venv-vision` (receta de la 009), con la trayectoria suavizada y aplicada con `sendcmd` sobre `crop`.
* D-4: normalizar con `loudnorm` en dos pasadas (medir y aplicar `linear=true`), con true peak ≤ -1 dBTP.
* D-5: recortar y unir con `trim`/`atrim` + `concat`/`xfade`/`acrossfade`, recodificando con `common/encode.py`.

## WARNING y PENDING

* WARNING: `012-yunet.md` (modelo y licencia) y `012-mejorar-voz.md` (cadena de filtros elegida).
* PENDING: ninguna.
