# 035: audio por hablante, corte sin rampa y filtro largo en archivo

- **Contexto**: `diarize.split` deja un WAV por hablante con silencio fuera de sus turnos (AC-5). El diseño pedía una rampa de 10 ms en cada borde contra los clics, pero no hay una medición de clics en este equipo todavía.
- **Elegida**: corte directo con `volume=enable='not(between(t,a,b)+…)':volume=0`, sin rampa. Si el filtro pasa de 30 000 caracteres, va en `<salida>.filter.txt` con `-filter_script:a`; probado con ffmpeg 7.0.2 y 2 000 turnos.
- **Descartadas**: rampa con `afade` por tramo (un filtro más largo y sin medición que la justifique); recortar con `atrim` y concatenar (cambia los tiempos que la 036 y la 037 usan).
- **Cómo revertir**: `server/src/content_studio/diarization/speaker_audio.py`, función `split_command`, y su rama de archivo.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/diarization/test_speaker_audio.py -q` (con ffmpeg real: largo y frecuencia conservados, cero fuera del turno). Antes de `main`: escuchar un clip y medir clics en la verificación final (FV).
- **Pendiente**: ninguno en PENDING; la medición de clics es de la FV de la 035.
