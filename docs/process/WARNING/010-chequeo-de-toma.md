# 010: chequeo automático de una toma (ciclo 3)

- **Contexto**: D-3 pide un chequeo (bordes, duración, pico, ruido, pausas y texto) que deja la toma en `ok` o `retake`. La spec da rangos, pero no las tolerancias ni qué hace el chequeo con los bordes («recorta los bordes a 0,4 s»).
- **Elegida**:
  - Tolerancias: pico entre −12 y −6 dB con ±1 dB; duración con ±0,5 s sobre el rango del estilo; bordes entre 0,2 y 0,6 s de silencio (la guía pide 0,3 a 0,5); pausa interna de más de 1 s; ruido si el nivel RMS de los primeros 0,3 s pasa de −50 dBFS; texto si las palabras mal dichas pasan del 15 % del guion (como `WER_MAX` en `voices/build.py`).
  - Los bordes se miden, no se recortan: el archivo no cambia. AC-5 copia la toma tal cual a la referencia, y recortar aquí rompería esa copia.
  - La razón `text` cuenta las palabras de cada diferencia que devuelve `compare.compare` (lo que se oye distinto), no los tramos.
  - whisper: el comando `whisper` con `WHISPER_MODEL` de la evaluación (`medium`). Si no está instalado, el chequeo lo anota (`whisper_missing`) sin cambiar el veredicto, y la toma se puede elegir a mano; así lo pide la spec.
  - El resultado va a `takes/<estilo>/<n>.check.json` y sale en stdout. Subir una toma encola `voice.check` (recurso `gpu`) y responde su `job`.
  - Las razones y los avisos son claves `voice.check.*` del catálogo en tres idiomas. Las claves aparecen como literales en `REASON_KEYS`, para que la etapa `i18n` las vea en uso.
- **Descartadas**:
  - Recortar los bordes a 0,4 s dentro del chequeo: cambiaría la toma que se elige y rompe AC-5.
  - Tratar `whisper_missing` como `retake`: la spec deja elegir la toma a mano sin whisper.
- **Pendiente en el ciclo**: `GET .../takes/{style}` sigue devolviendo solo los números de las tomas. El estado del chequeo se suma a esa respuesta en el ciclo 6, cuando la pantalla lo muestre.
- **Cómo revertir**: revertir el commit `feat: chequeo automático de una toma...`. Las tomas siguen guardándose y encolándose, sin chequeo.
