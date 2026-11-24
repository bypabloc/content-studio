# 021: el asistente recomienda Qwen3.5 9B, con el thinking apagado en los dos modelos

- **Contexto**: `python -m devtools llm-eval` (24/11/2026, RTX 4060 Laptop de 8 GB, contexto 8192, Q4_K_M, 25 casos por tarea). La primera corrida daba un empate (Gemma 98,7 %, Qwen 97,3–98,7 %), pero Gemma 4 E4B estaba pensando: devolvía `reasoning_content` con unos 700 tokens por pedido, aunque el sistema no llevara `<|think|>` (D-4 de la spec lo daba por apagado). Con `chat_template_kwargs.enable_thinking = false`, como Qwen, la comparación queda así:

  | Modelo | Revisar guion | Traducir en | Traducir pt | Latencia revisar | tok/s | VRAM pico |
  | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
  | qwen3.5-9b | 98,7 % | 100 % | 100 % | 3,1 s | 39 | 7847 MiB |
  | gemma-4-e4b (sin thinking) | 89,3 % | 100 % | 100 % | 2,1 s | 57 | 5461 MiB |
  | gemma-4-e4b (pensando) | 98,7 % | 100 % | 100 % | 17,0 s | 57 | 7147 MiB |

  La VRAM incluye de 2 a 3 GB del escritorio (apps abiertas), ocupados con la GPU libre.
- **Elegida**: `RECOMMENDED = 'qwen3.5-9b'` y el thinking apagado en los dos (`llm/models.py`). La diferencia en «Revisar guion» es de 9,4 puntos (más de 5), así que, por la regla de la spec, el ★ va al que más pasa. Las traducciones de Qwen también se leen mejor («Click the blue button labeled New Appointment» contra «schedule an appt.»). Con Qwen, las corridas reales tardan de 6 s (caption) a 47 s (publicar dos plataformas), con la carga incluida.
- **Descartadas**: Gemma pensando (iguala a Qwen, pero tarda 5 veces más y devuelve el razonamiento); Gemma sin thinking como ★ por su VRAM (pierde 9 puntos en la tarea principal). Gemma queda en el selector para equipos con menos VRAM libre.
- **Cómo revertir**: `RECOMMENDED` y `extra` de cada modelo en `server/src/content_studio/llm/models.py`.
- **Cómo comprobarla**: `python -m devtools llm-eval` (informe en `tmp/llm-eval/<fecha>/report.md`), que toma el turno de la GPU.
- **Pendiente**: [021-escucha-y-revision](../PENDING/021-escucha-y-revision.md): la puntuación humana de las 10 traducciones por modelo y la escucha de la narración revisada.
