# 016: sonoridad de mezclas con picos fuera de AC-3

**Qué falta.** AC-3 pide -14 ± 0,5 LUFS con TP ≤ -1 dBTP. Las mezclas reales quedan en -14,7 LUFS (transcript) y -14,8 (sidechain), con pico en -1,0 dBTP. El video `replace` queda en -15,6 LUFS con techo -2.

**Lo que se sabe (medido).**

- La normalización lineal de la 015 (`loudnorm`, dos pasadas) no llega al objetivo cuando la subida a -14 LUFS pasaría el techo: reduce la ganancia y el resultado queda por debajo.
- Reproducción mínima (sin mezcla real): con `ffmpeg` y la segunda pasada lineal de `normalize` (`loudnorm`, I -14, TP -1). Voz de 6 s con tono de 1 kHz a 0,2 en 0–1, 2–3 y 4–5 s, más un clic de 0,9 de 1 ms cada 0,5 s dentro de esos tramos; música rosa a -6 dB. Resultado: **-16,4 LUFS, TP -1,0**. Con un tono a 0,05 el crudo queda en -31 LUFS y no sirve como caso.
- Un limitador de pico antes de normalizar, con límite fijo, no llega a -14 en ese caso: con límites de -5,3 a -10 dBFS la salida queda entre -15,6 y -15,8 LUFS, con TP ≤ -1.
- Un límite fijo de -3 dBFS sobre la mezcla real normalizada (`mix.wav`, job 7) da -14,0 LUFS con TP -1,3. Es una prueba sobre la salida ya normalizada, no sobre el crudo del `render`.
- `loudnorm` en modo dinámico (`linear=false`) da el mismo resultado que el lineal en un caso extremo (tono 0,05, clics de 0,5 cada 50 ms): -20,4 LUFS y TP -1,0 en ambos. No resuelve el problema por sí solo.
- Un crudo en float (`pcm_f32le`) no cambia nada: el TP +0,5 es contenido real de la señal, no recorte.
- Un límite calculado una vez desde la medición del crudo (`techo − (objetivo − I_crudo) − 0,5`) no basta: limitar baja la sonoridad y la normalización posterior vuelve a subir la ganancia. En el caso extremo queda en -16,3 LUFS con TP +0,3 (sin limitar: -18,8 LUFS, TP +0,2).

**Opciones (decisión del usuario).**

1. Iterar el límite del limitador sobre el crudo (medir, bajar el límite, repetir hasta cumplir). No probado; el caso mínimo muestra que el límite fijo no basta.
2. Aceptar la desviación y cambiar AC-3 a ±1,5 LU para mezclas con picos. Es una decisión de la spec.
3. Dejar la mezcla como está (-14,7 / -14,8 LUFS) y ajustar el objetivo en la UI.

**Cómo comprobarlo.** `ffmpeg -i <mix.wav> -af ebur128=peak=true -f null -` sobre `out/mix/2026-11-22-7-mix-render/mix.wav` y `…-8-…/mix.wav`. Para el caso mínimo, el generador de la voz está descrito arriba; el experimento de límite fijo quedó en `tmp/spec-016/limitador-experimento.diff`.

**Dónde.** `server/src/content_studio/mix/render.py` (`render`), `server/src/content_studio/media/normalize.py` (`second_pass`, `measure`), `server/tests/unit/src/content_studio/mix/test_render.py` (test AC-3).
