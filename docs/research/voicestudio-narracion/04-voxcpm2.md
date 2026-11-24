# VoxCPM2: Clonación a 48 kHz con Instrucciones de Estilo

> Investigación del 2026-11-15. Qué es VoxCPM2 (OpenBMB), cómo se instala, sus modos de clonación, qué hacen las instrucciones `(…)` en español e inglés medido en la RTX 4060, y su licencia. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**, **medido** ([13](13-pruebas-en-gpu.md)); comunidad A/B/C.

---

## 1. Ficha

| Dato | Valor | Fuente |
| :--- | :--- | :--- |
| Arquitectura | Autorregresivo con difusión sobre AudioVAE V2, sin tokenizer; backbone MiniCPM-4 | README, arXiv 2606.06928 **(leída)** |
| Parámetros / pesos | 2B / ~5 GB (4.58 GB bf16 + 0.38 GB AudioVAE) | HF API **(leída)** |
| Salida | **48 kHz** (codifica la referencia a 16 kHz) | **(leída)**, **medido** |
| Idiomas | 30, incluido español | **(leída)** |
| Paquete | `voxcpm` 2.0.3 en PyPI (2026-05-11), Python 3.10–3.12 | PyPI **(leída)** |
| **Licencia** | **Apache-2.0 en código y pesos**, "free for commercial use" | Card de HF y technical report **(leída)** |
| VRAM medida | **5.75 GiB pico** (bf16, `load_denoiser=False`, `optimize=False`, frases cortas) | **medido** |
| Velocidad medida | RTF 0.9–4.5 en frases de 2–6 s (más lento que tiempo real); carga 102 s la primera vez | **medido** |

La cifra oficial de "~8 GB" se midió en una 4090 con `torch.compile` **(leída)**; sin compilar y sin denoiser, cabe en 8 GB con margen.

---

## 2. Instalación Standalone (Verificada)

```bash
uv venv -p 3.12 narration/.venv-voxcpm
VIRTUAL_ENV=narration/.venv-voxcpm uv pip install voxcpm soundfile
VIRTUAL_ENV=narration/.venv-voxcpm uv pip install "torch==2.14.1" "torchaudio==2.11.1"   # mismo segfault que OmniVoice con 2.15
```

```python
from voxcpm import VoxCPM
m = VoxCPM.from_pretrained('openbmb/VoxCPM2', load_denoiser=False, optimize=False)
# Clonación controlable (timbre + instrucción):
a = m.generate(text='(cheerful and energetic)Hoy te muestro algo nuevo.', reference_wav_path='ref.wav')
# Hi-Fi (máxima similitud, sin instrucción):
a = m.generate(text='Hoy te muestro algo nuevo.', reference_wav_path='ref.wav',
               prompt_wav_path='ref.wav', prompt_text='transcripción exacta')
sr = m.tts_model.sample_rate  # 48000
```

* `optimize=False` evita `torch.compile` y Triton; VoiceStudio lo desactiva por fallos de CUDA graphs en hilos (issue #3567 de VoiceStudio) **(leída)**.
* `load_denoiser=False` evita bajar ZipEnhancer de ModelScope (licencia sin verificar) y ahorra VRAM.
* VoiceStudio además usa `retry_badcase_max_times=1` y `max_len=min(4096, max(256, len(texto)*6))` para que una generación fallida no corra minutos **(leída, `voxcpm2_subprocess/main.py`)**.

---

## 3. Modos de Clonación

| Modo | Parámetros | Instrucción `(…)` | Uso |
| :--- | :--- | :--- | :--- |
| Controlable | `reference_wav_path` | **Se aplica** (no se lee) | Una referencia neutral + estilo por texto |
| **Hi-Fi / Ultimate** | `reference_wav_path` + `prompt_wav_path` + `prompt_text` | **Se lee en voz alta** | Máxima similitud y acento; la emoción sale de la referencia |
| Diseño | Sin referencia | Describe la voz | Voces de personaje |

**medido:** con Hi-Fi, `(tono alegre y enérgico)No puedo creer…` salió como "Tono alegre y enérgico, no puedo creer…" en las 2 semillas. La documentación dice que en Hi-Fi la instrucción "se ignora" **(leída)**: **conflicto**; en la práctica se pronuncia. Nunca mezclar Hi-Fi con instrucción.

---

## 4. Instrucciones de Estilo: Español vs Inglés

Prueba: `TEXTO = "No puedo creer lo que acaba de pasar. Todo cambió en un segundo."` con 5 instrucciones (alegre, triste, urgente, susurro, calma), en español y en inglés, 2 semillas, modo controlable.

| Hallazgo | Detalle |
| :--- | :--- |
| Ninguna instrucción se leyó en voz alta | Ni en español ni en inglés (whisper) |
| **En español cambian menos** | Con la misma semilla, la duración quedó **idéntica a la de la versión sin instrucción en 7 de 10** casos en español y en 3 de 10 en inglés |
| Ninguna es una copia de la base | Correlación de onda con la base 0.10–0.50 en ambos idiomas |
| Inglés con efecto visible en las métricas | `cheerful and energetic`: 3.2 s (vs 4.0 s base) y F0 mediana 250 Hz; `whispering`: rango de F0 de 5.4 st (vs 25 st base) |

Conclusión provisional: **escribir la instrucción en inglés**, como dice la documentación ("Chinese or English") **(leída)**. El juicio de si la emoción "suena" queda para la escucha del usuario ([13](13-pruebas-en-gpu.md) §6).

Formato recomendado por el cookbook **(leída)**: identidad, textura y escena en pocas palabras, al inicio y sin espacio: `(warm, confident, slightly faster)Hoy te muestro…`. Generar 1 a 3 tomas porque la adherencia varía.

---

## 5. Etiquetas y Texto en Español

| Prueba | Resultado medido (2 semillas) |
| :--- | :--- |
| Frase base, tutorial, drama con `…` | Transcripción exacta; **no omitió** el tramo tras `…` (OmniVoice sí) |
| Siglas (QR, IMC) | **Correctas** sin deletrear |
| Números en dígitos | Correctos ("1.500 pesos") |
| Homógrafos ("Hoy termino") | Whisper oyó "terminó" en 2 de 2: conviene la tilde y una prueba de escucha |
| Extranjerismos | "Apera el WhatsApp" en 1 de 2 |
| `[laughter]`, `[pause]` | No se leen |
| `[sigh]` | Altera el inicio ("Ah,", "¡Atrae!") |
| `[breath]` | No se lee, pero altera "Corrí" ("Corré", "Corí") |
| `<strong>` | **Se lee**: "Esto es strong importante" |

Las etiquetas del cookbook son `[laughing] [sigh] [Uhm] [Shh] [Question-*] [Surprise-*] [Dissatisfaction-hnn]` **(leída)**; `[laughter]` no está en la lista. Limpiar `* - ( )` del texto: un `(` dispara el modo instrucción y hay reportes de audio alucinado al final (issue #216, en español) **(leída)**.

---

## 6. Parámetros

| Parámetro | Valor | Nota |
| :--- | :--- | :--- |
| `cfg_value` | 2.0 (1.0–3.0) | 1.5–1.6 si una salida larga suena "buzzy" **(leída)**; con 1.6 la frase base salió igual de bien **medido** |
| `inference_timesteps` | 10 (4–30) | Más pasos, más detalle y más lento |
| `normalize` | `False` | Su normalizador apunta a chino e inglés; deletrear en el guion |
| `seed` | Parámetro propio de `generate` | Además se fijó `torch.manual_seed` |

No tiene parámetro de velocidad ni control fiable de pausas (issue #276) **(leída)**: las pausas largas se hacen fuera, como ya hace `tts.py`.

---

## 7. Comunidad

| Gusta | Se odia | Nivel |
| :--- | :--- | :--- |
| 48 kHz, Apache-2.0, diseño de voz | La voz cambia un poco según el texto, incluso en Hi-Fi (#231) | C |
| Mejor SIM en español en la tabla de los autores (83.1) | Peor WER en esa tabla (1.438) | B |
| es_419 en Soniqo: WER 5.8 % (mejor que Qwen 11.1 %) | Coseno 0.641 (menos parecido a la voz que Qwen 0.710) | B |
| | Alucina en frases de 1–2 palabras (#357); mucha memoria en la UI (#300) | C |

---

## 8. Veredicto para social-videos

* **El candidato principal para uso comercial** entre los motores de VoiceStudio: Apache-2.0, cabe en 8 GB y lee siglas y números mejor que OmniVoice y Qwen en las pruebas.
* **Dos modos útiles:** Hi-Fi con la referencia del estilo (conserva acento y entrega) para narración normal, y controlable con `neutral.wav` + instrucción en inglés para variar la emoción sin grabar otra referencia.
* **Costo:** más lento que tiempo real en la 4060 (RTF ~1–2.5) y una carga inicial de ~100 s.
