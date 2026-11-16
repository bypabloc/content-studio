# CosyVoice 3: Etiquetas, Instrucciones y Poca VRAM

> Investigación del 2026-11-15. Qué es Fun-CosyVoice3-0.5B (FunAudioLLM/Qwen), cómo se instala sin la app (con sus tres trampas en esta máquina), qué etiquetas e instrucciones funcionan en español medido en la RTX 4060, y su licencia. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**, **medido** ([13](13-pruebas-en-gpu.md)); comunidad A/B/C.

---

## 1. Ficha

| Dato | Valor | Fuente |
| :--- | :--- | :--- |
| Versión abierta | `FunAudioLLM/Fun-CosyVoice3-0.5B-2512` (dic-2025); el repo se movió a `QwenAudio/CosyVoice` | HF API, `gh api` **(leída)** |
| Arquitectura | LLM basado en Qwen → tokens de habla a 25 Hz → flow matching → vocoder HiFT | `cosyvoice3.yaml`, arXiv 2505.17589 **(leída)** |
| Pesos | Repo de 9.75 GB; para inferencia bastan ~5.4 GB | HF API **(leída)** |
| Salida | 24 kHz | **(leída)**, **medido** |
| Idiomas | zh, en, ja, ko, de, **es**, fr, it, ru + 18 dialectos chinos | Card **(leída)** |
| **Licencia** | Apache-2.0 en código y metadatos de los pesos; la card cierra con "for academic purposes only" (dos pedidos de aclaración sin respuesta) | **(leída)**: **conflicto** |
| VRAM medida | **3.5 GiB** pico (fp32) | **medido** |
| Velocidad medida | RTF ~1.0–1.8 en frases de 2–6 s | **medido** |

---

## 2. Instalación Standalone (Verificada, con Tres Trampas)

```bash
git clone --depth 1 --recursive https://github.com/FunAudioLLM/CosyVoice && cd CosyVoice
uv venv -p 3.10 .venv
# Quitar del requirements: torch, torchaudio, deepspeed, tensorrt, onnxruntime-gpu, el índice extra, openai-whisper y gradio
grep -v -i -E '^(torch|torchaudio|deepspeed|tensorrt|onnxruntime-gpu|--extra-index-url|openai-whisper|gradio)' requirements.txt > req.txt
VIRTUAL_ENV=.venv uv pip install "torch==2.14.1" "torchaudio==2.11.1" -r req.txt onnxruntime openai-whisper huggingface_hub "setuptools<80"
VIRTUAL_ENV=.venv uv pip uninstall wetext
.venv/bin/python -c "from huggingface_hub import snapshot_download; snapshot_download('FunAudioLLM/Fun-CosyVoice3-0.5B-2512', local_dir='pretrained_models/Fun-CosyVoice3-0.5B')"
```

| Trampa | Síntoma **medido** | Arreglo |
| :--- | :--- | :--- |
| `openai-whisper==20231117` fijado | El build falla: `No module named 'pkg_resources'` | Instalar `openai-whisper` sin versión (el frontend lo importa) |
| **setuptools ≥ 80** | `ErrorDuringImport … No module named 'pkg_resources'` al cargar el modelo | `setuptools<80` (VoiceStudio fija lo mismo por WhisperX, issue #224) |
| **`wetext`** | Al cargar descarga sus datos de ModelScope y recibe **HTTP 403** en bucle | Desinstalarlo: el frontend cae a "sin normalizador" (lo mismo hace VoiceStudio **(leída)**) |
| torchaudio 2.11 | `TorchCodec is required for load_with_torchcodec` al leer la referencia | Instalar `torchcodec` (exige FFmpeg 4–7) o reemplazar `torchaudio.load` por una lectura con soundfile, como hizo el banco de pruebas |

No es un paquete: se agregan el repo y `third_party/Matcha-TTS` al `sys.path`.

```python
import sys; sys.path[:0] = ['CosyVoice', 'CosyVoice/third_party/Matcha-TTS']
from cosyvoice.cli.cosyvoice import AutoModel
cv = AutoModel(model_dir='CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B')
SYS = 'You are a helpful assistant.'
# Mismo idioma, con transcripción de la referencia:
out = cv.inference_zero_shot(texto, f'{SYS}<|endofprompt|>{transcripcion}', 'ref.wav', stream=False, text_frontend=False)
# Instrucción (ignora la entrega de la referencia):
out = cv.inference_instruct2(texto, f'{SYS} Please speak in a sad and slow tone.<|endofprompt|>', 'ref.wav', stream=False)
audio = torch.cat([j['tts_speech'] for j in out], dim=1)  # 24 kHz
```

El prefijo `You are a helpful assistant.<|endofprompt|>` es **obligatorio**: sin él aparecen repeticiones u otro idioma (issues #1703, #1790) **(leída)**.

---

## 3. Texto en Español

| Prueba (2 semillas, `inference_zero_shot`) | Resultado **medido** |
| :--- | :--- |
| Frase base, tutorial, drama con `…`, anuncio, extranjerismos | Transcripción exacta |
| Siglas (QR, IMC) | Correctas sin deletrear |
| Números en dígitos, sin normalizador | Correctos ("1500 pesos"); con dígitos y letras whisper oye lo mismo |
| Homógrafos ("Hoy termino… Ayer terminó…") | Semilla 1: "termino… termino" (pierde la tilde de **terminó**); semilla 2: "terminó… terminó". Inestable en los dos sentidos |
| Pregunta `¿…?` | Sube: +3.9 y +10.0 st |
| Mayúsculas | Más lento con "MUY" (2.4 s vs 2.1 s); el efecto se confirma escuchando |
| Velocidad de la referencia | Copiada: 3.2 palabras/s en la frase base (referencia a 3.3) |
| `speed` 0.9 / 1.15 | +11 % / −13 % de duración |

El caso "números con el normalizador inglés" no se pudo medir: sin `wetext` no hay normalizador. Según el código, con `wetext` instalado todo texto no chino pasa por el normalizador **inglés** ("25" → "twenty-five") **(leída)**: otra razón para dejarlo fuera.

---

## 4. Etiquetas Inline

| Escrito | Resultado medido (2 semillas) |
| :--- | :--- |
| `[laughter]` | No se lee |
| `[sigh]` | No se lee |
| `[breath]` | No se lee (en 1 de 2 alteró "Corrí" → "Corrid") |
| `<strong>muy</strong>` | No se lee |
| `[pause]` | **Se lee** como "pausa" |

Es el único de los cuatro donde todas las etiquetas del tokenizer pasan sin leerse. Si la risa, el suspiro o la respiración **suenan** de verdad se decide escuchando ([13](13-pruebas-en-gpu.md) §6). Lista completa del tokenizer: `[breath] <strong></strong> [noise] [laughter] [cough] [clucking] [accent] [quick_breath] <laughter></laughter> [hissing] [sigh] [vocalized-noise] [lipsmack] [mn]` **(leída)**.

---

## 5. Instrucciones (`inference_instruct2`)

Texto "No puedo creer lo que acaba de pasar. Todo cambió en un segundo." con 5 instrucciones, en inglés (`Please speak in a … tone.`) y en español (`Por favor habla con …`), 2 semillas **medido**:

| Instrucción | Inglés | Español |
| :--- | :--- | :--- |
| Base sin instrucción (zero-shot) | 3.5–3.8 s, 3.5–3.7 palabras/s | — |
| Triste y lento | **5.2–5.8 s**, rango de F0 5.9–8.6 st (más plana) | 3.6–5.3 s |
| Urgente, rápido | **3.1–3.7 s**, hasta 4.2 palabras/s | 4.4 s y **8.7 s: leyó la instrucción** ("Esula habla con urgente, hablando rápido…") |
| Alegre | Pausas más largas (1.46 s) | Sin cambio claro |
| Susurro | Sin cambio claro de F0 (VoiceStudio: "style words such as whispering were not followed") | Sin cambio claro |
| Calma | Sin cambio claro | Sin cambio claro |

* **Escribir la instrucción en inglés.** En inglés nunca se leyó; en español se leyó 1 de 10 veces (issue #1903: las instrucciones largas se leen **(leída)**).
* `instruct2` **ignora la entrega de la referencia** (VoiceStudio **(leída)**): el timbre puede parecerse menos a la voz clonada.

---

## 6. Comunidad

| Gusta | Se odia | Nivel |
| :--- | :--- | :--- |
| Mejor similitud de hablante en español en CV3-Eval (78.85) | Repeticiones e inestabilidad frente a CosyVoice 2 (#1703, 29 comentarios) | B / C |
| `[breath]` directo | Japonés y ruso salen en chino (#1675, #1790) | C |
| Liviano, ecosistema activo | Instalación difícil (HF #1, #18) | C |

En español no apareció ninguna repetición ni cambio de idioma en las 70 generaciones de prueba **medido**.

---

## 7. Veredicto para social-videos

* **El mejor para respiraciones, risas y énfasis inline**, y el más liviano (3.5 GiB). Licencia Apache-2.0 con un *disclaimer* académico que conviene aclarar antes de usarlo en videos de clientes.
* **Modo recomendado:** `inference_zero_shot` con la transcripción para narración normal; `instruct2` con la instrucción **en inglés** y corta para cambiar la emoción.
* **Costo:** la instalación más frágil de las cuatro (tres arreglos manuales).
