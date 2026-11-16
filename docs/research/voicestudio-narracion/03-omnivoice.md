# OmniVoice: el Motor por Defecto de VoiceStudio

> Investigación del 2026-11-15. Qué es OmniVoice (k2-fsa), cómo se instala sin la app, qué controla, cómo rinde en español medido en la RTX 4060 y qué limita su licencia. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**, **medido** (prueba propia, [13](13-pruebas-en-gpu.md)); comunidad A/B/C.

---

## 1. Ficha

| Dato | Valor | Fuente |
| :--- | :--- | :--- |
| Arquitectura | Difusión discreta enmascarada, no autorregresiva; backbone Qwen3-0.6B; tokenizer de audio Higgs Audio (8 codebooks) | arXiv 2604.00688 **(leída)** |
| Parámetros / pesos | 0.6B / ~3.3 GB (2.45 GB modelo + 0.81 GB tokenizer) | HF API **(leída)** |
| Salida | 24 kHz mono | **(leída)**, **medido** |
| Idiomas | 646, incluido español (27 560 h de entrenamiento) | Paper, apéndice D **(leída)** |
| Paquete | `omnivoice` 0.2.1 en PyPI (2026-07-16), Python ≥3.10, exige `transformers>=5.3` | PyPI **(leída)** |
| **Licencia de pesos** | **CC-BY-NC** (por Emilia) + tokenizer bajo **Boson Higgs Audio 2 Community License** | Card de HF **(leída)**; autor en issues #235 y #258 **(leída)** |
| VRAM medida | **2.22 GiB pico** (fp16, frases cortas, con `ref_text`) | **medido** |
| Velocidad medida | RTF 0.6–1.8 en frases de 2–4 s (domina el costo fijo); carga 48 s la primera vez | **medido** |

---

## 2. Instalación Standalone (Verificada)

```bash
uv venv -p 3.12 narration/.venv-omnivoice
VIRTUAL_ENV=narration/.venv-omnivoice uv pip install omnivoice soundfile
# OBLIGATORIO en esta WSL: el torch 2.15 que resuelve uv da segfault en torch.cuda.is_available()
VIRTUAL_ENV=narration/.venv-omnivoice uv pip install "torch==2.14.1" "torchaudio==2.11.1"
```

* **medido**: con `torch 2.15.0` el proceso muere con *Segmentation fault* al consultar CUDA (driver de Windows, CUDA UMD 13.4). Con `2.14.1+cu130`, el mismo de `.venv-qwen`, funciona.
* Upstream recomienda `torch==2.8.0` de cu128 **(leída)**; no fue necesario.

```python
import torch
from omnivoice import OmniVoice
modelo = OmniVoice.from_pretrained('k2-fsa/OmniVoice', device_map='cuda', dtype=torch.float16)
prompt = modelo.create_voice_clone_prompt(ref_audio='ref.wav', ref_text='transcripción exacta')
torch.manual_seed(1)
audio = modelo.generate(text='Hola…', language='es', voice_clone_prompt=prompt, num_step=32)[0]  # np.ndarray 24 kHz
```

* Pasar **siempre `ref_text`**: sin ella carga Whisper large-v3-turbo y hay OOM reportados en 8 GB (issue #282) **(leída)**.
* `create_voice_clone_prompt` codifica la referencia una sola vez; VoiceStudio hace lo mismo (`generate_with_cached_ref`, `tts_backend.py`) **(leída)**.
* La semilla se fija con `torch.manual_seed` antes de cada llamada; VoiceStudio la reinicia por trozo de texto (issue #3730 de VoiceStudio) **(leída)**.

---

## 3. Controles

| Control | Cómo | Resultado medido |
| :--- | :--- | :--- |
| `language` | `'es'` o nombre | `'es'` y `None` dieron la misma duración y transcripción **medido** |
| `speed` | Factor (>1 más rápido) | 0.9 → +11 % de duración; 1.15 → −12 %. Funciona **medido** |
| `duration` | Segundos exactos; prioridad sobre `speed` | No probado |
| `num_step` | 32 (VoiceStudio "best quality"); 16 más rápido | Se usó 32 |
| `class_temperature` | 0 = codicioso; 0.3–0.7 para respiraciones y variación (VoiceStudio) | 0.5 no cambió duración ni transcripción en 2 semillas **medido** |
| `postprocess_output` | `True` quita silencios largos | Por defecto |
| `instruct` (solo diseño, sin referencia) | Vocabulario cerrado en inglés: género, edad, tono, `whisper`, acentos ingleses, dialectos chinos | `male, middle-aged, low pitch` y `male, whisper` funcionan (susurro: F0 sin sonoridad) **medido**. En español lanza `ValueError` según el código **(leída)** |

### 3.1 Etiquetas Inline

| Escrito | Resultado medido (whisper, 2 semillas) |
| :--- | :--- |
| `[laughter]` | No se lee: se ejecuta como gesto |
| `[sigh]` | No se lee |
| `[breath]` | **Se lee**: "bris", "breathe" |
| `<strong>muy</strong>` | **Rompe la generación**: 0.4 s de audio o solo "Esto es" |
| `[pause]` | **Rompe la generación**: 0.35 s de audio (whisper alucina "Gracias por ver el vídeo") |

Las 13 etiquetas válidas: `[laughter] [sigh] [confirmation-en] [question-en] [question-ah] [question-oh] [question-ei] [question-yi] [surprise-ah] [surprise-oh] [surprise-wa] [surprise-yo] [dissatisfaction-hnn]` (regex `_NONVERBAL_PATTERN` del paquete instalado **(leída)**). VoiceStudio implementa `[pause N]` **fuera del modelo** cortando el texto: nunca pasar `[pause]` al modelo.

---

## 4. Español: Lo que Salió Bien y Mal

| Prueba | Resultado (2 semillas) |
| :--- | :--- |
| Frase base, tutorial, anuncio, extranjerismos (WhatsApp, Zoom, stock) | Transcripción exacta |
| Pregunta `¿…?` | Sube al final (+1.3 a +3.0 semitonos) |
| Homógrafos sin tilde ("Hoy termino") | Whisper oyó "terminó" en 1 de 2: la regla de la tilde aplica |
| Siglas (QR, IMC) | "query" e "IMSC/IMSS": **deletrearlas** como en Qwen |
| Números en dígitos | Leídos bien ("veinticinco", "mil quinientos pesos") |
| **`…` en mitad de la oración** ("despacio… y no había nadie") | **Omitió "y no había nadie" en las 2 semillas**. También omitió "el texto" en 1 de 2 en otra frase. Coincide con el issue #253 (omite partes) **(leída)** |
| Mayúsculas ("MUY") | Sin efecto audible en la transcripción ni en la duración |

Bug conocido: se traga finales de palabra antes de coma o punto por el *fade* de 0.1 s entre trozos en textos largos (issue #116) **(leída)**; no se reprodujo en frases cortas.

---

## 5. Licencia

* "The pre-trained model is licensed under the CC-BY-NC due to constraints from its training data (e.g., Emilia)" **(leída, card)**.
* A un youtuber monetizado, el autor respondió: "we do not hold the rights to grant any commercial license" (issue #235, 2026-07-30) **(leída)**.
* El tokenizer exige mostrar "Built with Higgs Materials licensed from Boson AI" y una licencia ampliada por encima de 100 000 usuarios activos anuales **(leída)**.
* VoiceStudio lo registra como `noncommercial` **(leída)**.
* Decisión del usuario del 2026-11-15: **se incluye igual**, marcado como no comercial ([README](README.md#decisiones-tomadas)).

---

## 6. Comunidad

| Gusta | Se odia | Nivel |
| :--- | :--- | :--- |
| Calidad multilingüe: "clearly the best open model we have tried" (checo, #258); "IMO, the best TTS out there" (#116) | La licencia: varios youtubers se fueron (#235, #258, #275) | C |
| Muy rápido (RTF 0.025–0.09 en H100) | Omite o repite palabras (#253, #134); VRAM que crece por llamada (#199) | C |
| Mejor similitud de timbre en es_419 (coseno 0.758, Soniqo, 10 clips) | WER 9.9 % en es_419 (peor que VoxCPM2 y Chatterbox en esa prueba) | B |

---

## 7. Veredicto para social-videos

* **Sirve para:** pruebas, uso personal y videos no monetizados; frases cortas con risa o suspiro; voz susurrada por diseño.
* **No sirve para:** videos monetizados o de clientes (licencia). Tampoco para guiones con `…` a mitad de oración sin revisar con `--evaluar`.
* **Si se integra:** `language='es'`, `ref_text` siempre, `num_step=32`, semilla por bloque, nunca pasar `[pausa]`, `<…>` ni `[breath]` al modelo, y `--evaluar` obligatorio por las omisiones.
