# 015: seguir a la persona con YuNet (T4)

**Qué se decidió.**

- **Modelo**: `face_detection_yunet_2023mar.onnx` del repo de Hugging Face `opencv/face_detection_yunet`, con la revisión fija `3cc26e7f…`. El SHA-256 del archivo coincide con el que publica Hugging Face (`8f2383e4…`). Licencia MIT.
- **OpenCV**: `opencv-python==4.13.0.92`. Se eligió sobre la 5.x, recién salida, por el riesgo con `FaceDetectorYN`.
- **Trayectoria**: 5 muestras por segundo; media móvil de 1 s; el centro no se mueve más de 0,25 del ancho por segundo (AC-5). Sin cara se conserva la última posición; antes de la primera, el centro (0,5).
- **Entre varias caras**: las grandes (área de al menos la mitad de la mayor) y, entre ellas, la más cercana a la anterior.
- **Recorte**: `sendcmd` mueve `crop x` cada 0,2 s. El build de ffmpeg de este equipo no tiene la opción `eval` en `crop`: no se usa. El filtro toma las órdenes sin ella (verificado).
- **Receta `vision` en versión 2**: la versión 1 quedó a medias (ver PENDING `015-repair-primera-instalacion`). Subir la versión fuerza a rehacer todos los pasos.
- **Nombres de prueba**: el AC-5 nombra `test_face_track.py`; el plan manda `test_smooth.py` y, como espejo del módulo, `test_face_track_main.py`. La prueba `-m local` va en `server/tests/integration/test_face_track.py`.
- **Motor visible**: la receta aparece en la lista de motores (`list_engines`) como las demás, y se instala sin aceptar licencia (no está en el registro de narración).

**Verificado.**

- Unitarias en verde: `smooth` (4), `face_track_main` (4), `reframe` (incluido el AC-5 con ffmpeg real: mitad roja al principio, azul desde 0,8 s), `recipes`, `services` y `registry`.
- `-m local` con el motor instalado: un círculo que no es cara da la trayectoria en 0,5 con 10 muestras.
- Cara real, a mano (no se commitea): un video de 6 s en el que la cara pasa de la izquierda a la derecha a los 2 s. La trayectoria va de 0,32 a 0,76, sin pasos mayores de 0,05 (= 0,25 / 5). La imagen de prueba no declara licencia, así que solo sirvió para esta comprobación local.
- Pendiente: la prueba `-m local` con foto (se salta sin `server/tests/fixtures/vision/face.jpg`), ver PENDING `015-foto-de-prueba`.

**Arreglos encontrados en el camino.**

- `test_convert_render.py` era un huérfano del espejo desde T2 (`edddb93`): probaba `convert.py` con un nombre sin módulo. Se fusionó en `test_convert.py`, y la prueba real de ffmpeg se salta sin ffmpeg, como antes.
- `mypy` marcó `tuple(map(float, …))` como tupla de longitud variable: ahora un helper desempaqueta las cuatro coordenadas.
- El `pre-push` corre `typecheck` sobre el repo del commit: un error de tipos en código nuevo tumba también el test de hooks. Se corrigió antes de commitear.

**Dónde.** `server/src/content_studio/vision/{smooth,face_track_main}.py`, `media/reframe.py` (`follow-face`, `crop_xs`, `sendcmd_script`), `engines/recipes/vision.json`, `services/media_reframe_track.py`.
