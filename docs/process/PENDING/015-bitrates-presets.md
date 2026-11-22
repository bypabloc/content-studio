# 015: bitrates máximos de los presets de redes

**Qué queda.** D-2 pide que cada preset de redes traiga los bitrates máximos que documenta la plataforma, con las fuentes en WARNING. `media/presets.py` tiene tamaño, fps y encuadre, pero no bitrates.

**Por qué no se hizo.** Requiere leer la documentación actual de cada plataforma (Instagram, TikTok, YouTube Shorts, YouTube, X), que cambia, y no se verificó en esta spec.

**Qué hacer.** Buscar las cifras en la documentación oficial de cada plataforma, anotarlas con su URL y fecha en una ficha WARNING, y añadirlas a `presets.py` con una prueba que las compare.
