# 010: el tramo a importar se marca con inicio y fin en segundos, no como región sobre la onda (superada)

- **Contexto**: D-4 de la spec pide marcar el tramo de 8 a 12 s sobre la onda (`Waveform` con una región, plugin Regions de wavesurfer). La onda sale de `/media/peaks`, que pasa por `allowed_file`: solo lee rutas de `out/` y de las referencias. El archivo de origen (un video o audio del usuario) no pasa, así que su onda necesita un endpoint nuevo.
- **Elegida**: dos campos numéricos, inicio y fin en segundos, con el mismo límite de 8 a 12 s que valida el server. El error del tramo sale del catálogo (`error.invalid_span`), y el permiso del dueño es una casilla obligatoria.
- **Descartadas**: el endpoint de picos del origen dentro de este sub-paso (cambia el server, que ya pasó su gate, y amplía el alcance de 7c-3); tomar siempre los primeros segundos (no respeta el tramo que elige el usuario).
- **Cómo revertir**: añadir la región de wavesurfer sobre la onda del origen cuando exista el endpoint (ver la pendiente).
- **Cómo comprobarla**: `ImportReference.test.tsx`, «un tramo de menos de 8 s no deja importar, y lo dice con el rango del server».
- **Resuelta**: la región sobre la onda del origen se hizo en [010-region-sobre-la-onda](010-region-sobre-la-onda.md) (commit `e9e8e57`). La ficha PENDING `010-region-de-importar` se cerró.
