# 013: faster-whisper y Limpiador de silencios (audio y video)

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `013-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. **El limpiador nunca modifica el archivo de entrada**: siempre escribe uno nuevo en la carpeta del trabajo. Las pruebas usan medios generados en `tmp/spec-013/`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 25 archivos entre server y client) |
| Rama | `feature/013-whisper-cleaner` desde `origin/dev`, en `../content-studio-worktrees/013-whisper-cleaner/` |
| Depende de | [012](../012-engines-storage/README.md) (fusionada en `origin/dev`) |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Quitar los silencios de un audio o un video:

1. faster-whisper transcribe con los tiempos de cada palabra.
2. Los huecos de más de 500 ms se marcan para cortar, dejando 150 ms de margen.
3. El usuario revisa los cortes sobre la forma de onda y la línea de tiempo (con el video arriba si lo hay), los ajusta y renderiza.

El resultado es el archivo limpio (video con el corte exacto en el cuadro y crossfade de audio), la transcripción con los tiempos ya ajustados, un SRT, la lista de cortes para Premiere o DaVinci Resolve y un informe. faster-whisper reemplaza también al whisper de la evaluación de narración y del chequeo de tomas.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | faster-whisper: receta, modelos, servicio de transcripción y caché | PEN |
| 2 | Plan de cortes (puro) y reasignación de tiempos | PEN |
| 3 | Render de audio y video y exportaciones (SRT, EDL, XML, informe) | PEN |
| 4 | Client: selector de whisper, Limpiador con lote y revisión en la línea de tiempo | PEN |
| 5 | Migrar la evaluación y el chequeo a faster-whisper | PEN |

## Decisiones clave

* D-1: faster-whisper en su propio venv (`.venv-whisper`, receta de la 012), con los modelos small, medium, large-v3-turbo ★ y large-v3 descargados al usarlos.
* D-2: dos trabajos: `clean.analyze` (GPU, transcribe y propone los cortes) y `clean.render` (CPU y NVENC), con la revisión entre los dos.
* D-3: el plan de cortes es una función pura sobre las palabras, y replanificar con otros parámetros no vuelve a transcribir.
* D-4: transcripciones cacheadas en disco, con su ruta en la tabla `transcripts` (sin contenido en la base).
* D-5: exporta EDL CMX3600 y XML FCP7 (`xmeml`), porque Premiere y Resolve los importan.

## WARNING y PENDING

* WARNING: `013-cuda-windows.md` (cuBLAS y cuDNN por pip) y `013-render-precision.md`.
* PENDING: cierra `010-whisper-a-faster-whisper.md`.
