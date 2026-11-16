# IndexTTS 2.5: Emoción Graduable

> Investigación del 2026-11-15. Qué es IndexTTS 2.5 (bilibili), cómo se instala sin la app, cómo funcionan el vector de emoción, `emo_text` y `duration_factor` medido en la RTX 4060, qué hace con el texto en español y qué restringe su licencia. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**, **medido** ([13](13-pruebas-en-gpu.md)); comunidad A/B/C.

---

## 1. Ficha

| Dato | Valor | Fuente |
| :--- | :--- | :--- |
| Versión | IndexTTS-2.5 (pesos del 2026-08-10); IndexTTS-2 **no** soporta español | README, HF API **(leída)** |
| Arquitectura | GPT texto→semántico (~0.8B) → S2M con Zipformer → BigVGAN; códec a 25 Hz | arXiv 2601.03888 **(leída)** |
| Pesos | 5.49 GB (+ w2v-bert, campplus y bigvgan que baja en el primer uso) | HF API **(leída)** |
| Salida | **22 050 Hz** | `infer_v2_5.py` **(leída)**, **medido** |
| Idiomas | zh, en, ja, **es**, ar | README **(leída)** |
| **Licencia** | **bilibili Model Use License** (código y pesos): las salidas cuentan como obra derivada, prohíbe usarlas para mejorar otros modelos, ley china y arbitraje en Shanghái; el DISCLAIMER prohíbe el "uso comercial sin autorización" de forma ambigua | LICENSE, DISCLAIMER **(leída)**: **conflicto** |
| VRAM medida | **5.69 GiB** pico sin el Qwen de emoción; **6.79 GiB** con él | **medido** |
| Velocidad medida | RTF ~1.1–2.4 sin Qwen de emoción; **RTF ~10** con él (desborda a la RAM compartida) | **medido** |

---

## 2. Instalación Standalone (Verificada)

```bash
git clone --depth 1 https://github.com/index-tts/index-tts && cd index-tts
uv sync --python 3.11 --extra webui                 # sin deepspeed; trae torch 2.8 cu128 (funciona en esta WSL)
uv tool run --from 'huggingface_hub[cli]' hf download IndexTeam/IndexTTS-2.5 --local-dir=checkpoints
```

* En Linux instala `WeTextProcessing` (pynini) sin problemas en esta máquina **medido**.
* Para español llama a `nemo_text_processing`, que **no está en las dependencias**: el log dice `No module named 'nemo_text_processing'` y el texto pasa sin normalizar **medido**.
* Al cargar imprime ">> Low-VRAM mode enabled (8.0 GB < 10 GB), long text will be split into chunks" **medido**.

```python
import sys; sys.path.insert(0, 'index-tts')
from indextts.infer_v2_5 import IndexTTS2
tts = IndexTTS2(cfg_path='checkpoints/config.yaml', model_dir='checkpoints',
                use_bf16=True, use_cuda_kernel=False, use_deepspeed=False,
                use_qwen_emo=False)        # True solo para emo_text (+1.1 GiB)
tts.infer(spk_audio_prompt='ref.wav', text='Hola…', lang='es', output_path='out.wav',
          emo_vector=[0, 0, 0.8, 0, 0, 0, 0, 0], emo_alpha=0.6)
```

* **Sin transcripción**: `infer()` no recibe el texto de la referencia **(leída)**. La referencia se corta a 15 s.

---

## 3. Texto en Español: Lo que Hace el Modelo

| Prueba (2 semillas) | Resultado **medido** |
| :--- | :--- |
| Frase base, tutorial, drama con `…`, siglas (QR, IMC) | Transcripción exacta; siglas correctas sin deletrear |
| **Números en dígitos** ("1500 pesos") | **Mal**: "mil cimientos pesos", "500 pesos". En letras, bien |
| **Raya `—`** ("sin prisa, revisa el texto — y guarda") | **Leída como "menos"** en 2 de 2 |
| MAYÚSCULAS vs minúsculas | **Salida idéntica**: el código pasa todo el texto español a mayúsculas antes de tokenizar (`text.upper()`) **(leída)** |
| Homógrafo "Hoy termino" | Whisper oyó "terminó" en 2 de 2 (ver [13](13-pruebas-en-gpu.md) §6) |
| Pregunta `¿…?` | Sube fuerte al final: +7.9 y +10.1 st |
| Enumeración con "y" | El último cae 10.5–12.1 st respecto del penúltimo (como predice la fonética) |
| `[laughter]`, `[sigh]`, `[breath]`, `<strong>`, `[pause]` | **Todas se leen**: "Lotter", "SAI", "breath", "strong", "pause" |

### 3.1 Ritmo

* **No copia la velocidad de la referencia**: 2.0–2.4 palabras/s (~130 ppm) con una referencia a 198 ppm **medido**. Deja ~1 s entre oraciones y ~0.3–0.7 s en las comas.
* Es el motor más lento al hablar de los probados y el que más se acerca a los 130–160 ppm recomendados para explicativos ([09](09-entonacion-y-ritmo.md)).
* `duration_factor` 0.85 → −15 % de duración; 1.15 → +14 % **medido**.
* `max_text_tokens_per_segment` 60 y 120 dieron **salidas idénticas** en un texto de 3 oraciones **medido**: con 8 GB el modo de baja VRAM trocea igual. El truco del issue #775 (bajar a 60) no cambia nada en esta GPU.

---

## 4. Emoción

### 4.1 Vector de 8 Emociones

Orden `[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]`. El código de la WebUI aplica un sesgo por emoción y limita la suma a 0.8; `infer()` no lo hace y hay que aplicarlo a mano **(leída)**. Prueba con 0.8 en una sola emoción, normalizado, `emo_alpha=0.6`, texto "No puedo creer lo que acaba de pasar. Todo cambió en un segundo." **medido**:

| Emoción | Duración (s1 / s2) | Palabras/s | F0 mediana | Lectura |
| :--- | :--- | :--- | :--- | :--- |
| Sin vector (base) | 5.1 / 5.4 | 2.4–2.6 | 132–134 Hz | Referencia |
| Alegre | 5.6 / 6.1 | 2.1–2.3 | 144–146 Hz | Algo más aguda, pausa larga |
| Triste | 7.5 / 7.7 | 1.7–1.9 | 117–136 Hz | **Mucho más lenta** |
| Enojado | 5.5 / 6.5 | 2.0–2.2 | **176–182 Hz** | Más aguda; **perdió el "No" inicial** en 2 de 2 |
| Miedo | 4.6 / 4.6 | **2.8** | **176–191 Hz** | Más rápida y aguda |
| Sorpresa | 6.7 / 6.9 | 1.9 | 150–159 Hz | Pausas de 1 s |
| Calma | 5.7 / 5.7 | 2.3 | 122–126 Hz | Más grave |

El vector **cambia la entrega de forma medible** y coherente con la emoción. Si suena natural se decide escuchando ([13](13-pruebas-en-gpu.md) §6). Con `emo_alpha=1.0` (alegre) no hubo pérdida de palabras en este texto.

### 4.2 `emo_text`

* Requiere `use_qwen_emo=True`: un Qwen 0.6B que convierte el texto en el vector. Suma 1.1 GiB y en 8 GB **desborda: RTF ~10** **medido**.
* Instrucción en español vs inglés **medido** (1 semilla): "tono alegre y enérgico" y "cheerful and energetic" dieron **audio idéntico**; lo mismo "triste y lento" vs "sad and slow". "urgente, hablando rápido" vs "urgent, speaking fast" difirieron. El clasificador entiende el español en los casos simples.
* Conviene **el vector directo**: mismo efecto, sin el costo del Qwen.

### 4.3 Clip de Emoción

`emo_audio_prompt` toma la emoción de otro audio (incluso de otra persona) y conserva el timbre de la referencia, con `emo_alpha` como mezcla **(leída)**. No se probó por falta de clips de emoción propios.

---

## 5. Comunidad

| Gusta | Se odia | Nivel |
| :--- | :--- | :--- |
| Emoción graduada, única entre los motores de VoiceStudio | Retrocede frente a 2.0 en emoción y timbre (#759, #781, en chino) | C |
| Cross-lingual | Pedido de español latino sin respuesta (#805) | C |
| RTF 0.21 en 4090 (proveedor) | Cambiar la velocidad deja "tono y timbre muy raros" (#781) | B / C |

---

## 6. Veredicto para social-videos

* **Sirve para:** storytelling y piezas emocionales; es el único motor donde la emoción se gradúa sin regrabar. Su ritmo pausado encaja con explicativos.
* **No sirve sin preparar el texto:** números en letras, sin rayas `—` (usar comas o `…`), sin etiquetas de ningún tipo.
* **Licencia:** la más riesgosa de las cuatro para videos monetizados (obra derivada, jurisdicción china, *disclaimer* ambiguo).
* **Si se integra:** `use_qwen_emo=False` y emoción por vector; la VRAM queda en 5.7 GiB.
