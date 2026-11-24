# Prácticas de la Comunidad: Cómo Eligen y Preparan Voces Ajenas

> Investigación del 2026-11-17. Lo que hace la comunidad de TTS abierto con audio ajeno o derivado: de dónde saca las referencias, cómo elige y limpia el clip, qué trucos usa por motor (con foco en CosyVoice 3), cómo mide cuál es la mejor y qué discute sobre ética. Lo básico de grabarse uno mismo ya está en [voicestudio-narracion/11](../voicestudio-narracion/11-audio-de-referencia.md) y no se repite. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; evidencia A/B/C.

---

## 1. Resumen

* **De dónde**: LibriVox, colecciones curadas con licencia (Kyutai, Voice-Zero) y, cada vez más, **voz diseñada por texto** (VoxCPM2 Voice Design → WAV fijo), que es lo que los mantenedores de VoxCPM aprueban por escrito para uso comercial (B).
* **No denoisear por defecto**: mejorar el audio de la referencia sube la calidad pero **baja la similitud** (F5-TTS: UTMOS 3.51 → 3.89, SECS 0.35 → 0.28; A). Si hay ruido, medir antes y después.
* **Duración**: 7–12 s es el punto común. F5 recorta a 12 s, el Space de CosyVoice 3 recomienda ≤ 10 s y un paper midió más similitud con 7.7 s que con 5.5 s (A).
* **La cola de la referencia se cuela** en la salida en F5 y en Qwen3-TTS: la comunidad quita la última frase del clip (B/C).
* **Para elegir entre candidatas, se mide**: similitud de hablante (WavLM-SV o ERes2Net), WER con Whisper y UTMOS sobre las mismas frases. El método ExpPro lo formaliza y mejora el MOS frente a elegir al azar (A).

---

## 2. De Dónde Sacan las Referencias

| Fuente | Práctica | Evidencia |
| :--- | :--- | :--- |
| LibriVox | Recortar un capítulo de un buen lector (ver [03](03-librivox-en-espanol.md)) | B **(leída)** |
| **Kyutai `tts-voices`** | WAV originales y `*_enhanced` más embeddings, con licencia por carpeta ([05](05-donaciones-cc0-kyutai-y-voice-zero.md)) | B **(leída)** |
| **Voice-Zero** | 155 clips CC0 de LibriVox, procesados y listos para Chatterbox y Pocket TTS | B **(leída)** |
| **VoxCPM2 Voice Design** | Generar, guardar el WAV y reutilizarlo como `reference_wav_path`. Mantenedores (#407): "You may save the WAV files produced by Voice Design and reuse them long-term" | B **(leída)** |
| Qwen3-TTS VoiceDesign → Base | Diseñar una vez, guardar el WAV como "fuente de verdad" y cachear el prompt | C **(snippet)**, guías de terceros |
| Voces de demo (Chatterbox `mtl_prompts`, presets de Qwen) | Se usan, pero **sin licencia clara**: #574 (Chatterbox) y #353 (Qwen, voz "Sohee" en YouTube monetizado) no tuvieron respuesta oficial | C **(leída)** |
| YouTube, podcasts, packs sin ficha | Se usan, pero son **ilegales o de procedencia dudosa** | **(snippet)** |

---

## 3. Elegir y Preparar el Clip

### 3.1 Duración por Motor

| Motor | Recomendación | Evidencia |
| :--- | :--- | :--- |
| F5-TTS | "<|endofprompt|>12s and leave proper silence space (e.g. 1s) at the end"; recorta a ~12 s; límite total de 30 s | B **(leída)** README de `infer` |
| F5-TTS (bug) | Recortaba el audio a 12 s pero dejaba el `ref_text` completo, y repetía frases. Se corrigió en el PR #1328 (15/10/2026) | B **(leída)** |
| CosyVoice 3 | El Space oficial pide ≤ 10 s; el tokenizador ignora más de 30 s y la comunidad propone partir con VAD (#844) | B **(snippet)** / C **(leída)** |
| Chatterbox | Un mantenedor recomienda "at least 10 seconds", WAV ≥ 24 kHz, y que el estilo coincida con el uso (audiolibro → referencia de audiolibro). 5 min no mejoró | B/C **(leída)** #39 |
| Qwen3-TTS | La calidad "scales roughly linearly from 3 to 15 seconds, then plateaus" | C **(snippet)** |
| Paper (F5-TTS, BSC 2026) | SECS 0.35 con 7.7 s frente a 0.24 con 5.5 s: "a direct correlation between prompt length and speaker similarity" | A **(leída)** arXiv 2602.05770 |

### 3.2 Limpieza

| Hallazgo | Dato | Evidencia |
| :--- | :--- | :--- |
| **Mejorar sube la calidad y baja la similitud** | F5-TTS: UTMOS 3.51 → 3.89, DNSMOS Pro 3.11 → 3.31, **SECS 0.35 → 0.28** (mejora con Sidon, medido con VERSA) | A **(leída)** |
| Los modelos de *speech enhancement* meten artefactos | "even the SOTA SE models would introduce artifacts… and harm the TTS performance" | A **(snippet)** arXiv 2505.13830 |
| **Conflicto** | En flow matching, entrenar el modelo para tolerar ruido rinde más que limpiar el prompt (arXiv 2406.05699) | A **(snippet)** |
| UVR o demucs | Guías recomiendan "5_HP-Karaoke-UVR" y *de-reverb*. **No hay mediciones de similitud** | C **(snippet)** |
| Los artefactos del códec se clonan | La compresión Opus de Telegram "became part of the cloned voice" en F5 | C **(snippet)** |
| EQ y *de-esser* (F5) | Bajar la sibilancia (3–6 kHz en voces masculinas, 6–8 kHz en femeninas) mejora el resultado. Normalizar el volumen "increase[s] the inference's successful rate" | C **(leída)** #378 |
| No remuestrear hacia arriba (F5) | SWivid: "a true 24kHz but not a resampled one" | B **(leída)** #965 |
| Voice-Zero procesa todo (RNNoise, Kanade, Resemble Enhance) | En el banco, su clip procesado clonó igual que el crudo ([05](05-donaciones-cc0-kyutai-y-voice-zero.md) §3.1) | **medido**, 1 caso |

### 3.3 Corte y Transcripción

| Truco | Evidencia |
| :--- | :--- |
| Empezar y terminar en silencio, nunca a mitad de palabra; `ref_text` termina en "." (F5 #85). El que preguntó dijo que "didn't seem to make much difference" → **conflicto** | C **(leída)** |
| La última frase de la referencia se filtra a la salida (F5 #85; Qwen3-TTS #341, con un ejemplo en español). Remedio: quitar la frase final del clip | B/C **(leída)** |
| Qwen3-TTS cambia de hablante si el idioma de la referencia y el de la salida no coinciden (#80): regenerar | C **(leída)** |
| El Space de CosyVoice 3 transcribe solo y deja editar | B **(snippet)** |

---

## 4. Trucos de CosyVoice 3

Todo sale de `example.py` oficial **(leída)** y de issues de `QwenAudio/CosyVoice` (el repo `FunAudioLLM/CosyVoice` redirige ahí).

| Tema | Detalle | Evidencia | En este repo |
| :--- | :--- | :--- | :--- |
| Prefijo obligatorio | `'You are a helpful assistant.<|endofprompt|>\|<|endofprompt|>' + transcripción` | B | `SYS_COSYVOICE` en `tts.py` |
| Instrucción | `inference_instruct2(texto, 'You are a helpful assistant. <|endofprompt|>instrucción><|endofprompt|>\|<|endofprompt|>', wav)`. **Ignora la entrega de la referencia** | B | Lo usa `voces.py` para los estilos |
| Instrucción dentro del prefijo de zero-shot | `"You are a helpful assistant. {instrucción}<|endofprompt|>\|<|endofprompt|>{transcripción}"` (#1895, sin respuesta oficial) | C | **Medido: casi no cambia la entrega** ([10](10-pruebas-en-gpu.md) §5) |
| **Cross-lingual** | `inference_cross_lingual('You are a helpful assistant.<|endofprompt|>\|<|endofprompt|>' + texto, wav)`, **sin transcripción**: una voz en español habla inglés | B | Genera `neutral-en` en las voces en español del catálogo |
| Speaker guardado | `add_zero_shot_spk(prompt_text, prompt_wav, spk_id)` + `save_spkinfo()`, y luego `inference_zero_shot(text, '', '', zero_shot_spk_id=…)`. **No promedia varios clips** | B | No se usa |
| Similitud oficial | `speech_eres2net_sv_en_voxceleb_16k` (ModelScope), coseno entre prompt y salida (#1010) | B | Se usó WavLM-base-plus-sv |
| Fine-tuning en español | `examples/libritts` y RL/GRPO, sin receta para español (#830, #1278) | B/C | Fuera de alcance |

---

## 5. Cómo Elegir la Mejor Referencia con Números

| Métrica | Herramienta | Quién la usa | Evidencia |
| :--- | :--- | :--- | :--- |
| Similitud (SIM) | WavLM-large ajustado para verificación (`cal_sim.sh`) | seed-tts-eval, el estándar de facto | A **(snippet)** |
| SIM | ERes2Net | CosyVoice | B **(leída)** |
| SIM | "WavLM y ERes2Net often produce different system rankings": usar dos | Qwen-Audio-3.0-TTS | A **(snippet)** |
| WER/CER | Whisper-large-v3, Paraformer-zh, NeMo | seed-tts-eval, BSC | A |
| Calidad | UTMOS, DNSMOS Pro (vía VERSA) | BSC | A **(leída)** |

**ExpPro** (arXiv 2409.18512, A **(leída)**), probado con CosyVoice y GPT-SoVITS sin reentrenar:

1. **Filtro estático**: agrupa por pitch (K-Means) y puntúa con DNSMOS y coherencia texto-emoción; queda el 15 % superior.
2. **Prueba con el modelo**: cada candidata sintetiza 20 frases y se combinan CER, SIM (Resemblyzer + WavLM) y similitud de emoción (emotion2vec).
3. **Elección dinámica**: entre 5 finalistas, la que tiene el texto más parecido al que se va a narrar.

Frente a elegir al azar en CosyVoice: MOS 4.13 → 4.45 (feliz) y SP 0.733 → 0.867 (enojo).

**Lo que se aplicó aquí** ([10](10-pruebas-en-gpu.md)) es la versión mínima: las mismas frases con cada candidata, y medir WER (whisper `large-v3-turbo`), SIM (WavLM-base-plus-sv) y UTMOS.

---

## 6. Ética

| Proyecto | Postura | Evidencia |
| :--- | :--- | :--- |
| VoxCPM | Apache cubre el modelo, no el audio. Exige "lawful authorization" para toda referencia y recomienda etiquetar la IA | B **(leída)** |
| Chatterbox | Marca de agua PerTh en toda salida. Un paper (SoK, 2025) muestra que ninguna marca resiste todos los ataques | B / A **(snippet)** |
| Hugging Face | La Content Policy no menciona la clonación. Propone un **"voice consent gate"**: el hablante lee en vivo una frase de consentimiento generada al momento y un ASR la verifica | B **(leída)** |
| Kyutai | Pide leer una frase de consentimiento en cada donación ([05](05-donaciones-cc0-kyutai-y-voice-zero.md)) | **medido** |
| NVIDIA (Hi-Fi TTS) | Pidió consentimiento escrito aunque el audio era dominio público | **(leída)** |

Leyes y plataformas: ver [02](02-derechos-copyright-y-voz.md).
