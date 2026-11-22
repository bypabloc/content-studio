# 015: escucha y revisión del usuario

**Qué falta.** Escuchar y mirar las salidas reales de la spec, y decidir los gustos que no se pueden medir. Las rutas están en `out/spec-015/` del checkout principal (ver [015-verificacion-final](../WARNING/015-verificacion-final.md)).

**Escuchar.**

- **Normalización con y sin «mejorar voz»**: `normalizar/job-23` (narración, `podcast`) frente a `job-24` (con mejorar voz); `job-25` frente a `job-26` (`youtube`). Y la música: `job-27` a `job-30`.
- **Video normalizado**: `normalizar/job-32` (final, `youtube`). `job-31` es el mismo video antes del ajuste de pico (−0,8 dBFS), y `job-33` es el experimento a −1,5 dBTP.
- **Unión con fundido cruzado**: `api/job-41-concat` (28 s). Revisar los cruces en 9–10 s y 18–19 s.
- **Convertir**: `convertir/job-1` a `job-15` (MP3 V2, FLAC y OGG Opus del lote de 5).

**Mirar.**

- **Redes**: `cuadros/reels-<modo>-{2,12,22}.png` para los cinco encuadres. `redes/job-16` (centro), `job-17` (barras), `job-18` (desenfoque), `job-19` (manual, franja derecha) y `job-22` (seguir a la persona, sin caras). `cuadros/concat.png` es el espectrograma de la unión.
- **Capturas** de Convertir y Normalizar en claro y en oscuro: `capturas/`. Son dos pantallas: la spec no tiene pantalla de recortar y unir (D-6).

**Decisiones de gusto.**

- **Techo de pico con pérdida.** Con −2 dBTP, el video queda en −15,4 LUFS (1,4 LU bajo `youtube`). Con −1,5 dBTP quedaría en −14,9 LUFS, con 0,3 dB de margen para el AAC. Si se prefiere −1,5, es la constante `LOSSY_TRUE_PEAK` con su prueba.
- **Cadena de «mejorar voz»**: es la de D-4 y no tiene alternativa en la spec. Si se quiere más suave o más fuerte, se ajusta `ENHANCE` en `normalize.py`.

**Observaciones de la revisión de capturas** (no bloquean):

- Contraste bajo del texto secundario en la fila de trabajo de Normalizar («Antes», «Después», «Listo», «Escuchar», «Abrir carpeta»), en claro y en oscuro.
- Con el cuadro de prueba de 1×1 px, la vista previa de Convertir se ve como un hueco de unos 1000 px. Hay que confirmar la altura con un cuadro real.

**Pendiente de otra entrega.** Seguir a la persona con una cara real: [015-foto-de-prueba](015-foto-de-prueba.md).

**Cómo se verifica.** Escucha del usuario en las rutas de arriba, y una captura de Convertir con un video real, revisada por `image-reader`.
