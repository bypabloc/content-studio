# 021: el asistente recomienda Gemma 4 E4B (empate de chequeos con Qwen3.5 9B)

- **Contexto**: `python -m devtools llm-eval` (24/11/2026, RTX 4060 Laptop de 8 GB, contexto 8192, Q4_K_M) con los 25 casos de cada tarea:

  | Modelo | Revisar guion | Traducir en | Traducir pt | Latencia revisar | tok/s | VRAM pico |
  | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
  | gemma-4-e4b | 98,7 % | 100 % | 100 % | 17,0 s | 57 | 7147 MiB |
  | qwen3.5-9b | 97,3–98,7 % | 100 % | 100 % | 3,1 s | 38–39 | 7847 MiB |

  La VRAM incluye unos 3,1 GB del escritorio (apps abiertas) que ya estaban ocupados con la GPU libre. Los dos caben con 8192 de contexto.
- **Elegida**: `RECOMMENDED = 'gemma-4-e4b'` en `llm/models.py`. La diferencia de chequeos es menor de 5 puntos (empate); los dos son Apache 2.0, así que decide el más liviano: Gemma deja unos 1000 MiB libres y Qwen solo 340, que una app del escritorio puede agotar y mandar el modelo a la RAM compartida.
- **Descartadas**: Qwen3.5 9B como ★ por su latencia en «Revisar con IA» (3 s contra 17 s; Gemma escribe respuestas más largas): la regla de la spec pone primero el margen de VRAM, y Qwen queda elegible en el selector.
- **Cómo revertir**: cambiar `RECOMMENDED` en `server/src/content_studio/llm/models.py`.
- **Cómo comprobarla**: `python -m devtools llm-eval` (informe en `tmp/llm-eval/<fecha>/report.md`), con el turno de la GPU.
- **Pendiente**: la puntuación humana de las 10 traducciones por modelo, que el informe deja para el usuario; si Qwen gana claro, cambia el ★.
