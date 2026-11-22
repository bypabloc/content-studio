# 013: decisiones del plan de cortes y del render de audio

- **Contexto**: la spec deja al agente los casos de borde del plan y el formato del render de audio. Se eligió lo que no pierde voz y es verificable.
- **Elegida**:
  - Sin palabras no hay cortes (`plan([]) == []`): sin transcripción no se sabe qué es voz, y cortar todo el archivo lo borraría entero.
  - Un tiempo dentro de un corte se pega al inicio del corte al reasignarlo (`remap`), para que las palabras no caigan fuera del limpio.
  - Los cortes de menos de 50 ms se descartan; un corte cuyo margen se come el hueco tampoco se propone.
  - Crossfade de 15 ms entre tramos (`acrossfade`); un tramo de menos de 30 ms recibe `afade` de entrada y salida, porque `acrossfade` no lo puede fundir.
  - El grafo de audio va en `audio-filter.txt` junto al resultado (`-filter_complex_script`), para no pasar el límite de la línea de comandos de Windows.
  - El WAV sale en PCM de 24 bits; cualquier otro formato, en AAC a 192 kbps.
- **Descartadas**:
  - Cortar todo el archivo cuando no hay palabras: borraría voz que no se transcribió.
  - Un `afade` en todos los tramos: cambia el sonido de los cortes normales sin necesidad.
- **Cómo revertir**: los cambios están en `clean/plan.py` y `clean/render.py`; se revierten con el commit de T1 (`785374f`) y T3.
- **Cómo comprobarla**: `pytest server/tests/unit/src/content_studio/clean` (25 pruebas en verde, con los doctests de `plan.py` y `render.py`). Medición real de AC-3 con ffmpeg: duración 3.570 s (esperada 3.570 s), silencio más largo 0.285 s (límite 0.800 s), pico −6.00 dBFS.
- **Pendiente**: nada.
