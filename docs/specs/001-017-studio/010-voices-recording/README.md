# 010: Voces (perfiles propios y catálogo) y Grabar (kit guiado con micrófono)

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `010-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas usan un perfil nuevo `spec-010` y `tmp/spec-010/`. **Excepción pedida por el usuario**: `move-data` **mueve** las referencias actuales a `reference/<perfil por defecto>/`, sin borrar nada.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 25 archivos entre server y client, más el borrado de `grabar/`) |
| Rama | `feature/010-voices-recording` desde `origin/dev`, en `../content-studio-worktrees/010-voices-recording/` |
| Depende de | [009](../009-icons/README.md) (fusionada en `origin/dev`) |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Gestionar las voces desde el estudio:

* **Mis voces**: perfiles propios, cada uno con su kit de 12 estilos, que se graba con el micrófono en una sesión guiada (teleprompter, vúmetro, chequeo automático con whisper y varias tomas) o se importa desde un archivo con permiso del dueño.
* **Catálogo**: voces libres con su ficha y licencia, muestra por estilo, construir desde la cola y favoritas.

El CLI interactivo `grabar/` desaparece.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Perfiles en el server y migración del juego actual | PEN |
| 2 | Tomas: subir, chequear, elegir e importar | PEN |
| 3 | Catálogo: API, construir como trabajo y favoritas | PEN |
| 4 | Client: Mis voces, Grabar y Catálogo | PEN |
| 5 | Borrar `grabar/` y el grupo `legacy` | PEN |

## Decisiones clave

* D-1: perfiles en `reference/<profile>/` con `profile.json`. El juego actual se migra como el perfil `default` (paso 3 de `move-data`).
* D-2: captura PCM con AudioWorklet y WAV de 48 kHz, mono y 24 bits codificado en el client, sin procesado del navegador.
* D-3: el chequeo de una toma es un trabajo `voice.check` (recurso `gpu` por whisper) que mide bordes, duración, pico, ruido y texto.
* D-4: construir voces del catálogo es un trabajo `voice.build` en la cola.
* D-5: el permiso del dueño se guarda en `profile.json` (fecha y texto aceptado) y es obligatorio al importar.

## WARNING y PENDING

* WARNING: `010-captura-pcm.md` y `010-permiso-microfono-webview2.md`.
* PENDING: cierra `002-cspell-excepciones-temporales.md`. Deja `010-whisper-a-faster-whisper.md`, que cierra la 013.
