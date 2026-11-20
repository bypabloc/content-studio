# 010: marcar el tramo a importar sobre la onda, como región de wavesurfer

- **Qué**: D-4 pide elegir el tramo de 8 a 12 s sobre la onda del archivo de origen. Hoy el tramo se escribe en segundos (inicio y fin).
- **Por qué no se hizo**: `/media/peaks` solo lee rutas de `out/` y de las referencias (`allowed_file`). La onda del origen necesita un endpoint de picos que acepte esa ruta, con su propio gate del server.
- **Cuándo**: antes de publicar la 010 (T9), o en la 016 si el usuario lo acepta así.
- **Quién**: agente.
- **Qué la cierra**: una región arrastrable sobre la onda en `ImportReference.tsx`, con su prueba del tramo, y el endpoint de picos del origen.
