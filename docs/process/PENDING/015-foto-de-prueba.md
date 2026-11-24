# 015: foto con cara de licencia clara para la prueba `-m local`

**Qué queda.** `server/tests/integration/test_face_track.py::test_ac5_yunet_finds_a_real_face_in_the_test_photo` se salta mientras no exista `server/tests/fixtures/vision/face.jpg`. Hace falta una foto frontal con licencia clara (CC0, dominio público o permiso escrito del dueño), con su procedencia anotada en el mismo directorio.

**Por qué no se hizo.** La búsqueda no encontró una con licencia verificada. La imagen `examples/selfie.jpg` del Space `opencv/face_detection_yunet` no declara licencia. `david1.jpg` y `david2.jpg` de `opencv_extra` tampoco, y el `LICENSE` de esa rama no se pudo leer. Lena y Messi se descartaron.

**Qué hacer.** Elegir la foto, o pedir permiso a su dueño, guardarla en `server/tests/fixtures/vision/face.jpg` con su origen, y correr `uv run pytest -m local server/tests/integration/test_face_track.py`. La detección con una cara real ya se comprobó a mano (ver WARNING `015-seguir-a-la-persona`).
