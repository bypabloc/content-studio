# 015: presets de redes y encuadre fijo (T3)

**Qué se decidió.**

- **El ★ por proporción**: `presets.recommended(aspect)` da Reels si la proporción (ancho sobre alto) es menor de 0,8; cuadrado si está entre 0,8 y 1,25; y YouTube 1080 en el resto.
- **Encuadre como grafo**: `reframe.graph` arma un `-filter_complex` que lee `[0:v]` y deja `[v]` del tamaño pedido. `build` lo usa cuando `options` trae `reframe`, y entonces ignora la resolución de T2. El audio entra con `-map 0:a?`.
- **Modos fijos**: `center` escala para cubrir y recorta al centro; `manual` recorta con coordenadas normalizadas y escala; `fit-bars` escala para entrar y rellena con el color; `fit-blur` pone la imagen borrosa al fondo y la nítida encima, centrada.
- **Sin `GET /media/frame` todavía**: el endpoint del cuadro para la vista previa va en la T7, que es donde la pantalla lo usa.
- **Lo que queda**: los bitrates máximos por plataforma de D-2 no están en los presets. Van con sus fuentes, en la T9 o en la pantalla, según el PENDING `015-bitrates-presets`.

**Verificado.** `test_reframe.py` (AC-4): 1080×1920 en los tres modos fijos; en barras, la franja de arriba es roja; en desenfoque, la franja de arriba tiene más de diez colores. `test_presets.py`: el ★ por proporción, los datos de Reels, Shorts y YouTube 4K, y que cada preset traiga tamaño, fps y encuadre. 43 pruebas en `media/` en verde.

**Dónde.** `server/src/content_studio/media/presets.py`, `media/reframe.py`, `media/convert.py` (`build`).
