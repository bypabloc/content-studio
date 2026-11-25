# 028: arranque en frío: app-check y api up pueden tardar más de 30 s

- **Qué**: (a) `python -m devtools app-check run` falló en 2 de 5 corridas, las dos primeras tras compilar el binario: en la primera sección del pase de luz, una petición a la API no terminó en 30 s (`tests/e2e/app-check/fixture.ts`, `settled`). Las otras 3 pasaron (pase de luz de unos 7 s). El error ahora nombra la URL pendiente. (b) Una vez, `studio api up` respondió «el server no contestó en 30 s» justo después de un `api down`; el reintento arrancó en 3,5 s.
- **Por qué no se hizo**: `logs/server.log` queda casi vacío (uvicorn no registra accesos), así que no se vio qué petición colgó. No se sabe si fue el primer arranque tras compilar (antivirus o caché) o una petición lenta del server en frío.
- **Cuándo**: después de publicar.
- **Quién**: agente.
- **Qué la cierra**: repetir `app-check run` cinco veces con el binario ya compilado; si el error nombra una URL, medir esa ruta. Si no reaparece, cerrar la ficha.
