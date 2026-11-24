# 021: límites de Publicar por plataforma

- **Contexto**: «Publicar» valida en código los largos de cada plataforma (D-4). Son datos en `server/src/content_studio/llm/platforms.json`.
- **Elegida**: YouTube con título de 100, descripción de 5000, 15 hashtags y capítulos; Instagram Reels con 125 para la primera línea, 2200 de texto y 30 hashtags; TikTok con 150, 4000 y 10 hashtags. Tres títulos por plataforma. Capítulos solo en YouTube: el primero en 0:00, al menos 3 y separados por 10 s o más, en el inicio de un segmento real. Si no caben (un video de menos de 30 s), se omiten.
- **Descartadas**: dejar los límites al modelo (no los respeta siempre); un solo pedido para todas las plataformas (un schema más grande y un error en una invalida todas).
- **Cómo revertir**: editar `platforms.json`; los límites se leen al cargar el módulo.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/llm/tasks/test_publish.py`.
- **Pendiente**: si una plataforma cambia sus límites, se actualiza el JSON.
