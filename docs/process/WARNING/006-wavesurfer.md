# 006: wavesurfer.js 8.1.0 dibuja la onda con los picos del server

- **Contexto**: AC-8 pide que al terminar, el reproductor muestre la onda. El server ya calcula los picos (`/media/peaks`, grupo 2), así que el WebView no tiene que decodificar el audio.
- **Elegida**: `wavesurfer.js` fijado a `8.1.0` (versión exacta, como el resto de dependencias del cliente), con `peaks` del server y `url` para reproducir con el `<audio>` del WebView. El bundle sigue dentro del budget (`budget` pasa), así que no hace falta importación diferida.
- **Descartadas**: una onda en un `<canvas>` propio (más código, y sin regiones ni zoom para la 010 y la 011); decodificar el audio con Web Audio (lento, y carga el archivo entero en memoria).
- **Cómo revertir**: quitar la dependencia de `client/package.json` y cambiar `client/src/shared/media/Player.tsx` por un `<audio controls>`.
- **Cómo comprobarla**: `client/tests/unit/src/shared/media/Player.test.tsx` y `python -m devtools test-runner --type=budget`.
- **Antes de**: el merge a `dev`.
