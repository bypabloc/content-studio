# 016: el ducking del audio va con asendcmd y objetivo `volume@duck`

- **Contexto**: la spec pide `sendcmd` sobre el volumen de la música. En ffmpeg, `sendcmd` es el filtro de video; el de audio es `asendcmd`, con la misma sintaxis. El objetivo por tipo (`volume`) alcanza a todos los filtros `volume` del grafo, incluido el de la voz; medido: con un `volume` sin nombre en otra rama, la voz también cambiaba.
- **Elegida**: `asendcmd` con las órdenes `<t> volume@duck volume <factor>;` y el filtro de la música nombrado `volume@duck`. La ruta del archivo va entre comillas con el `:` de la unidad escapado una vez (`f='C\:/…'`), como el encuadre de 015 (`common/sendcmd.py`, compartido). Sin comillas, el `:` se pierde.
- **Descartadas**: `volume` sin nombre (afecta a la voz); `volume` con `eval=frame` y una expresión por tramos (el grafo crece con cada región y el ducking deja de ser editable como lista); el objetivo `duck` a secas (no alcanza al filtro: medido, sin efecto).
- **Otras decisiones de T1–T2**:
  - La música entra con 1 s de fade y sale con 2 s (o un tercio de la mezcla si es corta), como `music/duration.fit`. Descartado no hacer fade de entrada: la voz arrancaría con la música a todo volumen.
  - Los pasos de volumen son cada 20 ms y solo donde el volumen cambia (en 8 s, 91 órdenes: las rampas).
  - `amix` con `dropout_transition=0`: al terminar la voz, la música no se reajusta.
  - Sidechain: la voz de control se rellena con `apad` hasta la duración total. Sin eso, `sidechaincompress` corta la salida al terminar la voz (medido: 7 s en lugar de 8 s).
- **Cómo revertir**: los commits `693172c` (envolvente) y `aaf6fb8` (render).
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/mix` (AC-3: caída de unos 12 dB dentro de los tramos; AC-4: longitud exacta y `music_too_short`).
- **Pendiente**: ninguno; la medición real va en la verificación final.
