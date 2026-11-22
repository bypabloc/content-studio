---
modulo: edit
actualizada: 2026-11-22
---

# Recortar, unir y dividir

## Qué resuelve

Recorta un tramo de un audio o de un video (o quita ese tramo y une el resto), une varios archivos con un fundido cruzado y divide un archivo en partes. Es el núcleo que usará el Editor (017–019); esta spec no tiene pantalla propia.

## Qué hace hoy

- `uv run studio trim <archivo> --start S --end E [--mode keep|remove] [--fade-in S] [--fade-out S]`: conserva el tramo, o lo quita y une lo que queda. `remove` reusa el render del limpiador, así la duración es exacta.
- `uv run studio concat <archivos...> [--crossfade S]`: une en el orden dado, con fundido cruzado opcional entre archivos.
- `uv run studio split <archivo> (--markers T... | --every S) [--copy]`: parte en los tiempos dados o cada S segundos. Con `--copy` no recodifica y los cortes caen en cuadros clave.
- Salidas en `out/media/`: el audio sale en WAV y el video en MP4. La entrada no se modifica.
- La API tiene los mismos trabajos (`media.trim`, `media.concat`, `media.split`) en la cola.

## Dónde vive

- Código: `server/src/content_studio/media/edit.py`, `services/media_{trim,concat,split}.py`, `cli/media.py` y las rutas de medios en `api/routes/media.py`.
- Pruebas: `server/tests/unit/src/content_studio/media/test_edit.py`, `services/test_media_trim.py` y `test_media_concat.py`, y `cli/test_media.py`.
- Decisiones: WARNING [015-recortar-unir-dividir](../WARNING/015-recortar-unir-dividir.md).

## Historial

- 2026-11-22: spec 015 (T6 y T8): recortar, unir y dividir en el servidor y la CLI. La pantalla de edición queda en el Editor (017–019).

## Verificación

- Pendiente: corridas reales de cada operación y su medición (duración, volumen, espectrograma), en T9.
