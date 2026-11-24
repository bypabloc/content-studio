# 011: categorías de los 126 presets y catálogo de estilos en la API

- **Contexto**: el buscador de la sección Música agrupa los presets por familia. Los presets no tenían categoría, solo nombre, tonalidad, BPM y compás.
- **Elegida**: `music/categories.py`. La categoría sale del primer segmento del nombre (`lofi-jazz` → `lofi`) con un mapa explícito agrupado por familia (`FAMILIES`, que da `BY_PREFIX`) y unas excepciones por nombre completo (`OVERRIDES`: `deep-focus` → ambient, `tropical-house` → electronic). No hay clave `'code'` en el mapa: el gate de textos la toma por un código de error. Lo que no tiene familia es `genres`. `styles.py` suma `category` a cada preset al armar `STYLES`, y `styles_catalog(samples)` devuelve la lista para la UI con `has_sample` (si existe `samples/<estilo>.wav`). `GET /music/styles` la expone.
- **Mood, descartado**: la spec lo deja como opcional («si el caption lo deja claro»). Con 126 captions escritos a mano, no hay un criterio que no sea adivinar. Sale fuera de alcance; el filtro de la UI usa solo categoría, BPM y modo.
- **Por qué un módulo aparte**: `styles.py` ya tenía 264 líneas y el límite de la fuente es 300. El mapa de prefijos va en `categories.py`.
- **Cómo revertir**: quitar `category` de `STYLES` y el módulo `categories.py`; quitar la ruta de `api/routes/music.py` y su línea en `app.py`.
- **Cómo comprobarla**: `music/test_categories.py` (todo preset tiene categoría válida; los casos ambiguos), `music/test_styles.py` (126 entradas, `has_sample` según el disco) y `api/routes/test_music.py` (`GET /music/styles`, AC-4).
