# 013: el plan corta silencios audibles y el video corta en cuadros

- **Contexto**: con el video de prueba de 232 s (voz real de narraciones), el limpio quedaba con tres huecos de 0,82 a 1,26 s, que AC-11 no admite. Whisper ubica las palabras con sus tiempos y el audio puede callar más de lo que dicen (en un caso, la palabra «corto.» termina en 190,18 s y el audio calla desde 189,6 s). Además, el audio del video se separaba del video: cada corte redondeaba distinto al cuadro (hasta 0,36 s de desfase en 28 cortes).
- **Elegida**:
  - El plan corta, además de los huecos entre palabras, cada silencio audible (medido con `silencedetect` a -50 dB) más largo que `min_gap`, con el mismo margen de `padding` a cada lado. Los tramos que se tocan se unen.
  - El video se corta en cuadros: cada tiempo de corte se ajusta al cuadro como lo elige `trim` (`on_frame_grid`), y el audio usa esos mismos instantes. El informe y las exportaciones (EDL, XML) usan esa misma cuadrícula, así que la duración del informe coincide con la del archivo.
  - Ni el video ni el audio solo usan `acrossfade`: cada tramo lleva su fade de entrada y de salida de 15 ms y se une con `concat` sin solaparse. Con crossfade, cada unión quita 15 ms: en la narración de 32,7 s (6 uniones) el audio medía 27,588 s y el informe decía 27,678 s, y los subtítulos y el EDL quedaban 90 ms corridos. Esto cambia el texto de D-4 («crossfade de audio»): es una decisión técnica del implementador, anotada aquí.
- **Descartadas**:
  - Ampliar cada hueco de palabras hasta el silencio que lo contiene: no alcanza cuando el hueco de palabras es menor que `min_gap` (el caso de «corto.»).
  - Bajar `min_gap` por defecto (500 ms): cambia la política de cortes del usuario y corta pausas de lectura naturales.
  - VAD como detector de silencios: el servicio de faster-whisper ya usa `vad_filter` para transcribir, pero no devuelve los silencios. Se usa `silencedetect`, que ya está en el proyecto.
- **Cómo revertir**: los commits de los fixes 1–6 de T9 (render_main, audio de video, cuadrícula, silencios del plan y del análisis, informe).
- **Cómo comprobarla**:
  - Pruebas: `uv run pytest server/tests/unit/src/content_studio/clean/test_plan.py` (silencio audible, el que contiene un hueco) y `test_render_main.py` (sincronía a medio cuadro, cortes fuera de cuadrícula, informe igual al archivo).
  - Corrida real: `uv run studio clean tmp/spec-013/charla-prueba.mp4 --auto`. Resultado: cero huecos de 0,8 s o más en el limpio, video y audio a 3 ms, y el informe igual al video (208,800 s).
  - Clics: en las 41 uniones del audio limpio (16 kHz mono, ±50 ms alrededor de cada corte), el mayor salto entre muestras es 0,31 veces el percentil 99,9 de todo el audio; ninguna unión lo supera. En el espectrograma, las líneas oscuras en los cortes son los fundidos de 15 ms, no clics.
- **Pendiente**: la escucha del usuario. El margen de 150 ms y el umbral de -50 dB pueden recortar consonantes suaves al final de una palabra; si pasa, se sube el margen o se baja el umbral (son dos números).
