# 016: Mezcla de voz y música con ducking (y video opcional)

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `016-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. La mezcla nunca modifica las pistas de entrada. Las pruebas usan medios generados en `tmp/spec-016/`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Medium (unos 12 archivos entre server y client) |
| Rama | `feature/016-mix-ducking` desde `origin/dev`, en `../content-studio-worktrees/016-mix-ducking/` |
| Depende de | [015](../015-convert-normalize-trim/README.md) (normalize y edit), fusionada en `origin/dev` |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Poner la música bajo la voz. El ducking sale de la transcripción (rampas editables en la línea de tiempo) o de un compresor sidechain. Se puede configurar el volumen relativo, la intro y el outro, y el LUFS final, escuchar la vista previa en el navegador antes de renderizar y, opcionalmente, sumar la mezcla a un video (reemplazando su audio o por debajo de él). Las pistas llegan del historial, de archivos, de «Mandar a Mezclar» o de una música generada a medida.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Envolvente de ducking desde la transcripción (pura) | DON |
| 2 | Render: envolvente o sidechain, intro y outro, ajuste de la música, LUFS final y video (AC-3 con picos: PENDING) | DON |
| 3 | Client: Mezcla con línea de tiempo, rampas y vista previa WebAudio (sin probar con la app real: PENDING) | DON |

## Decisiones clave

* D-1: `mix/envelope.py` (puro) pasa de las palabras a los tramos de voz y de ahí a una curva de ganancia por tramos lineales.
* D-2: el render aplica la curva con `sendcmd` sobre `volume`, o `sidechaincompress` si se elige, y después `amix` y la normalización de la 015.
* D-3: la vista previa usa WebAudio `GainNode` con la misma curva que devuelve el server: no hay otra implementación del ducking en el client.

## WARNING y PENDING

* WARNING: `016-valores-ducking.md` (atenuación, rampas y márgenes por defecto; salida a 48 kHz; techo por códec).
* PENDING: `016-lufs-real-fuera-de-ac3.md` (LUFS -14 con TP ≤ -1 no se cumple con mezclas de picos), `016-escucha-y-capturas.md` (escucha, capturas, ducking medido y corrida de la UI real).
