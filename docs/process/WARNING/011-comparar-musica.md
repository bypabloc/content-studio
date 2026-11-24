# 011: comparar y elegir pistas de música (AC-8)

- **Contexto**: el plan pedía mover `CompareTakes` a `shared/components/` y generalizarlo con columnas configurables. Hoy `CompareTakes` de narración lee cada toma con `useTake` (guion, `.json` de semilla y evaluación). Las pistas de música salen de otro sitio: un `tracks.json` por trabajo con varias pistas.
- **Elegida**:
  - `features/music/MusicCompare.tsx` con sus propias columnas (estilo, variante, duración real, aviso `music_short`, voz, LUFS, tonalidad y BPM), en lugar de generalizar el de narración. Razón: solo hay dos usos y tienen fuentes distintas; una abstracción compartida antes del tercer uso sería la que la regla de código prohíbe. El de narración no se toca y sus pruebas siguen verdes.
  - Los datos de cada pista van en `tracks.json` de la carpeta del trabajo, escrito por `music/manifest.py` al final de `music_main`: duración real con ffprobe, aviso `music_short`, voz (`null` si no hubo evaluación), LUFS con ebur128, tonalidad y BPM del preset.
  - «Elegir» llama `POST /jobs/{id}/choose` con el archivo. La elección queda en `chosen` del mismo `tracks.json`: como cada pedido es un solo trabajo, hay una sola ★ por grupo.
  - Un pedido de varios estilos y varias variantes es **un** trabajo; sus pistas comparten `group_key` (`music:` + sha1 de los parámetros sin la semilla).
  - «Mandar a Mezclar» se ve deshabilitado: lo habilita la 016.
- **Descartadas**:
  - Un trabajo por pista: complicaba la clave de grupo y el número de trabajos en la cola sin ganar nada para la comparación.
  - Guardar la elección solo en la base de datos: la carpeta del trabajo ya tiene todo lo demás, y el `starred` de narración asume una toma por trabajo.
- **Cómo revertir**: quitar `features/music/MusicCompare.tsx`, `music/manifest.py`, la ruta `choose` en `api/routes/jobs.py` y las dos llamadas a `write_manifest` en `music_main.py`.
- **Cómo comprobarla**: `client/tests/unit/src/features/music/MusicCompare.test.tsx` (4 pistas de 2 estilos y 2 variantes; «Elegir» manda el archivo correcto), `server/tests/unit/src/content_studio/music/test_manifest.py` (duración, variante, aviso y voz con ffmpeg real), y `api/routes/test_jobs.py` (`choose`: pista válida, archivo ajeno y trabajo que no es de música).
- **Pendiente**: la generalización de `CompareTakes` se hará si aparece un tercer uso. El botón «Mandar a Mezclar» se habilita en la 016.
