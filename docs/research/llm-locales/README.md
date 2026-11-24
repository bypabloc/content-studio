# LLM locales para content-studio: Gemma 4 y Qwen (noviembre de 2026)

Investigación del 2026-11-18 para la spec 019 (hoy la 021, `local-llm-assist`; su carpeta la borró la 023 y está en el historial de git). El equipo es una RTX 4060 Laptop con 8 GB de VRAM y unos 32 GB de RAM, que corre un modelo a la vez en la GPU y trabaja en español neutro latinoamericano.

**Cómo leer este documento**: los benchmarks, tamaños y licencias son datos del fabricante. Las pruebas de traducción y de offload las midieron terceros. Los tok/s son estimaciones. **No hay ningún benchmark de español específico**, así que el modelo por defecto se decide con una prueba propia (spec 017, AC-10).

## 1. Qué cabe en 8 GB

| Modelo | Licencia | Entrada | GGUF Q4_K_M | ¿Cabe en 8 GB con 8–16k de contexto? |
| :--- | :--- | :--- | :--- | :--- |
| `google/gemma-4-E4B-it` (4.5B efectivos) | Apache 2.0 | texto, imagen, audio (30 s), video | 4,98 GB ([unsloth](https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF)) | Probable, sin medición |
| `Qwen/Qwen3.5-9B` | Apache 2.0 | texto, imagen, video | 5,68 GB ([unsloth](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF)) | Sí con 8k (prueba casera). Calculadoras dan 8–12k como techo |
| `google/gemma-4-12B-it` | Apache 2.0 | + audio | 7,66 GB | No, en la práctica |
| Gemma 4 26B-A4B (MoE), 31B, Qwen3.6-27B, 3.6-35B-A3B y 3.8-27B | Apache 2.0 | texto, imagen y video | 16,8–22 GB | No en GPU. Con offload, ~3–5 tok/s |

## 2. Calidad (benchmarks del fabricante)

| Modelo | MMLU-Pro | MMMLU (multilingüe) | GPQA Diamond | Otros |
| :--- | :--- | :--- | :--- | :--- |
| Gemma 4 E4B-it | 69,4 | 76,6 | 58,6 | MMMU Pro 52,6 |
| Qwen3.5-9B | 82,5 | 81,2 | 81,7 | MMLU-ProX 76,3; WMT24++ 72,6 |

* **Traducción**: en un post de r/LocalLLaMA que traducía a seis idiomas (entre ellos español), Gemma 4 superó a Qwen en COMET. El autor advierte que usó temperatura 0, no los muestreos recomendados ([Towards AI](https://pub.towardsai.net/i-tested-four-local-ai-models-on-a-literary-translation-gemma-4-won-with-a-catch-1f73ab357abb)).
* **Quejas**: Qwen3.5 sobrepiensa y entra en bucles con thinking, y `presence_penalty` no se aplicaba por la API de Ollama ([issue](https://github.com/ollama/ollama/issues/14493)). Gemma 4 E4B tuvo problemas de tooling (cuantización de capas PLE en MLX y plantillas GGUF actualizadas en abril) y una anécdota de visión pobre frente a Qwen3.5-4B.
* **Thinking**: Gemma 4 lo activa con el token `<|think|>` en el system prompt. Qwen3.5 lo tiene activo por defecto y se apaga con `chat_template_kwargs: {enable_thinking: false}`.
* **Muestreo recomendado**: Gemma 4 usa temperatura 1.0, top_p 0.95 y top_k 64. Qwen3.5 sin thinking usa 0.7, 0.8 y 20.

## 3. Runtime en Windows

| Runtime | Para qué | Salida estructurada |
| :--- | :--- | :--- |
| `llama-server` (llama.cpp, binarios CUDA de `ggml-org/llama.cpp`) | Embeber como proceso hijo, con API compatible con OpenAI | JSON schema convertido a gramática (subconjunto) |
| Ollama | Más fácil para desarrollo | `format` con JSON schema (GBNF) |
| LM Studio | Pruebas manuales con GUI | Gramáticas de llama.cpp |

Elegido: `llama-server`, arrancado bajo demanda y apagado al terminar, para respetar el turno de la GPU.

## 4. Recomendación para este equipo

* **Por defecto (provisional)**: Gemma 4 E4B-it Q4_K_M. Es el más liviano, multilingüe y multimodal, y en traducción le fue mejor según la comunidad.
* **Alternativa**: Qwen3.5-9B Q4_K_M para las reglas del guion que exigen razonamiento, siempre sin thinking.
* **Descartados en 8 GB**: los de 12B en adelante, por VRAM o por velocidad.
* **Pendiente de prueba propia**: unos 50 segmentos reales de guion y subtítulos con los dos modelos (spec 019).

## Fuentes

[Gemma 4 collection](https://huggingface.co/collections/google/gemma-4) · [gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it) · [gemma-4-12B-it](https://huggingface.co/google/gemma-4-12B-it) · [gemma-4-26B-A4B-it](https://huggingface.co/google/gemma-4-26B-A4B-it) · [gemma-4-31B-it](https://huggingface.co/google/gemma-4-31B-it) · [Lanzamiento de Gemma 4](https://9to5google.com/2026/04/02/google-gemma-4/) · [Qwen en Hugging Face](https://huggingface.co/Qwen) · [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) · [Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B) · [Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B) · [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) · [unsloth Qwen3.5-9B GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF) · [unsloth Gemma 4 E4B GGUF](https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF) · [bartowski Gemma 4 12B GGUF](https://huggingface.co/bartowski/gemma-4-12b-it-GGUF) · [Qwen3.5 en RTX 4060 8 GB](https://dev.to/plasmon_imp/i-pitted-3-qwen35-models-against-each-other-on-an-rtx-4060-8gb-what-spec-sheets-dont-tell-you-ko0) · [Estimaciones de willitrunai](https://willitrunai.com/can-run/gemma-4-26b-a4b-on-rtx-4060-8gb) · [Salida estructurada en LM Studio](https://lmstudio.ai/docs/developer/core/structured-output) · [llama.cpp en Windows](https://knightli.com/en/2026/05/18/llama-cpp-windows-cuda-vulkan-gguf/)
