# 030: las carpetas de entrada no se probaron en OneDrive ni en una unidad de red

- **Qué**: AC-2 a AC-8 se verificaron con carpetas locales de `tmp/spec-030/`. Una carpeta sincronizada por OneDrive o una unidad de red puede tardar en escribir y cambiar la fecha de un archivo de otra forma.
- **Por qué no se hizo**: en este equipo no se probó una carpeta de OneDrive ni de red, y no se escribió en la carpeta del usuario sin pedirlo.
- **Cuándo**: antes de publicar, con una carpeta sincronizada real.
- **Quién**: usuario (elige la carpeta).
- **Qué lo cierra**: `studio inbox add` sobre esa carpeta, un WAV soltado y su recibo en `done/`.
