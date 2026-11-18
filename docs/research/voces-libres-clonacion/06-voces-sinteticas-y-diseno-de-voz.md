# Voces Sintéticas y Diseño de Voz como Referencia

> Investigación del 2026-11-17. Si la salida de una voz predefinida de un TTS abierto (Piper, Kokoro, Parler…) o una voz diseñada por texto (VoxCPM2, Qwen3-TTS VoiceDesign) sirve como referencia para clonar, con qué licencia, y por qué las APIs comerciales quedan descartadas. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**, **medido**.

---

## 1. Resumen

| Veredicto | Candidatos |
| :--- | :--- |
| **Apta (datos CC0 o dominio público)** | Piper `es_MX/ald` (Unlicense), `es_ES/davefx` (CC0), `es_ES/carlfm` (PD, solo x_low), `en_GB/cori` (CC0), `en_US/ljspeech` (PD), `en_US/kristin`, `norman` y `john` (LibriVox, PD) |
| **Apta con matiz (permisiva, pero no CC0)** | Voz diseñada por texto (VoxCPM2, Qwen3-TTS VoiceDesign); Kokoro-82M; Parler-TTS; MeloTTS; StyleTTS2 LJSpeech; Qwen3-TTS CustomVoice; CosyVoice SFT; Chatterbox (voz por defecto); Piper `sharvard`, `mls_*`, `libritts`, `daniela`, `claude` |
| **Descartada** | XTTS-v2 (CPML), F5-TTS (CC BY-NC), Piper `lessac`, `ryan`, `hfc_female`, `amy`; Microsoft Azure/Edge, Google Cloud TTS, ElevenLabs |

* **En español latino, la única voz predefinida con datos CC0 o de dominio público es Piper `es_MX/ald`** **(leída)**. En el banco clonó bien (SIM 0.989/0.975, WER 0), pero su referencia estaba **saturada** (pico real +0.2 dBTP) y es de prosodia plana (105 ppm, UTMOS 2.95) **medido**.
* **La voz diseñada por texto es la vía más limpia frente al derecho a la voz**, porque no pertenece a nadie identificable. Pero **no es CC0**: es salida sin autor humano de un modelo Apache-2.0 ([02](02-derechos-copyright-y-voz.md) §4.1). El usuario pidió solo CC0 o dominio público, así que queda como alternativa documentada, fuera del catálogo.

---

## 2. Piper (`rhasspy/piper-voices`)

Cada voz trae un `MODEL_CARD` con el dataset y su licencia. **El modelo base cuenta**: varias voces se afinaron desde otra y heredan su licencia de datos **(leída)**.

| Voz | Dataset | Licencia | Base | Veredicto |
| :--- | :--- | :--- | :--- | :--- |
| **`es_MX/ald`** (medium) | `rmcpantoja/Ald_Mexican_Spanish_speech_dataset` | **Unlicense** | `rdh` (nl_BE, un hablante flamenco, CC0) | **Apta** |
| `es_MX/claude` (high) | Space `HirCoir/Piper-TTS-Spanish` | apache-2.0 | — | Con matiz: no dice de quién es la voz → **conflicto** |
| `es_ES/davefx` (medium) | OHF-Voice/voice-datasets | CC0 | `rdh` (CC0) | Apta, **peninsular** |
| `es_ES/carlfm` (x_low) | carlfm01/my-speech-datasets | Public domain | Desde cero | Apta, pero 16 kHz: mala referencia |
| `es_ES/sharvard` (medium) | Sharvard (Edinburgh) | CC BY 3.0 | `hifi_tts_92` | Con matiz |
| `es_ES/mls_10246` (low) | MLS | CC BY 4.0 | `en_US/ryan` (**CC BY-NC-SA**) | Descartada: el base es NC |
| `es_AR/daniela` (high) | OpenSLR 61 | CC BY-SA 4.0 | — | Con matiz; rioplatense |
| `en_US/ljspeech` (high) | LJ Speech | Public domain | — | **Apta** |
| `en_US/kristin`, `norman` (medium) | LibriVox | Public domain | Desde cero | **Apta** |
| `en_US/john` (medium) | LibriVox | Public domain | Kristin | **Apta** |
| `en_GB/cori` (high) | OHF-Voice/voice-datasets | CC0 | `rdh` (CC0) | **Apta**, británica |
| `en_US/lessac` | Blizzard 2013 | "exclusively for Research Purposes only" | — | **Descartada** |
| `en_US/ryan`, `en_US/hfc_female` | RyanSpeech, Hi-Fi-CAPTAIN | CC BY-NC-SA 4.0 | — | **Descartada** |
| `en_US/amy` | mimic3-voices | "See URL", sin licencia por voz | — | Descartada: no verificable |

**Medido con `es_MX/ald` medium** (`piper` en un venv aparte, texto del kit `neutral` acortado a 10.9 s):

| Dato | Valor |
| :--- | :--- |
| Referencia | 22 050 Hz, −15.2 LUFS, **pico real +0.2 dBTP** (satura), piso −38 dB, 105 ppm, UTMOS 2.95 |
| Clon con CosyVoice 3 | SIM 0.989/0.975, WER 0, UTMOS 3.49/2.91; la voz ajena más parecida dio 0.867 |

Como referencia sirve, pero el clon hereda la prosodia plana y el leve zumbido del vocoder **(no verificado** al oído**)**. No entró al catálogo: hay voces humanas CC0 mejores ([05](05-donaciones-cc0-kyutai-y-voice-zero.md)).

---

## 3. Voz Diseñada por Texto

| Motor | Cómo | Licencia y postura | Marca |
| :--- | :--- | :--- | :--- |
| **VoxCPM2** (ya en `narration/`) | Descripción entre paréntesis: `(A young woman, gentle and sweet voice)Hello…`. "results may vary between runs; generating 1–3 times is recommended" | Apache-2.0. Los mantenedores aprueban guardar y usar comercialmente el WAV de Voice Design (issue #407). Prohíbe "impersonation, fraud, or disinformation" | **(leída)** |
| **Qwen3-TTS VoiceDesign** (1.7B) | El README documenta "Voice Design then Clone": diseñar un clip y construir con el Base un prompt reutilizable | Apache-2.0. Hay preguntas abiertas sobre la licencia de la salida (#353, #375, #388) sin respuesta | **(leída)** |

Receta, si algún día se acepta una referencia que no es CC0 pero tampoco es de nadie:

1. Pedir el acento de forma explícita ("Latin American Spanish, neutral accent").
2. Generar de 3 a 5 candidatas y elegir una estable de unos 10 s.
3. **Congelar ese WAV** como referencia, porque el diseño cambia entre corridas.
4. Registrar el prompt, el modelo, la versión y la fecha.

El riesgo residual es que, con 2 millones de horas de datos de entrenamiento no publicados, una descripción muy específica se acerque a un hablante real (memorización). Es poco probable y no hay estudio que lo mida para VoxCPM2 **(no verificado)**.

---

## 4. Otras Voces Predefinidas

| Modelo | Licencia | Voces y matiz | Marca |
| :--- | :--- | :--- | :--- |
| Kokoro-82M | Apache-2.0 | Español: `ef_dora`, `em_alex` y `em_santa`, con un "thin" support. Los datos incluyen audio sintético de proveedores cerrados; un post afirma que es casi todo ElevenLabs y OpenAI → **conflicto** de procedencia | **(leída)** / **(snippet)** |
| Parler-TTS Mini (multilingual) | Apache-2.0 | Español: Steven, Olivia y Megan, lectores de LibriVox vía MLS y CML-TTS (CC BY 4.0) | **(leída)** |
| MeloTTS-Spanish | MIT | Un solo speaker `ES`; datos no declarados | **(leída)** |
| StyleTTS2 LJSpeech | Código MIT, pesos sin licencia en HF | Pide avisar a los oyentes que es sintético | **(leída)** |
| Qwen3-TTS CustomVoice | Apache-2.0 | Ryan y Aiden en inglés; ninguna voz nativa en español | **(leída)** |
| CosyVoice SFT | Apache-2.0 | Solo `CosyVoice-300M-SFT` (英文女, 英文男…); nada en español | **(leída)** / **(snippet)** |
| Chatterbox | MIT | Voz por defecto (`conds.pt`) de origen no documentado; toda salida lleva la marca de agua PerTh. Las voces de demo están en un bucket sin licencia (issue #574 sin respuesta) | **(leída)** |

---

## 5. Descartadas por Licencia o Términos de Uso

| Servicio | Cláusula | Marca |
| :--- | :--- | :--- |
| **Coqui XTTS-v2** (CPML) | "Non-commercial purposes include any of the following uses of the model **or its output**…". Coqui cerró: no hay a quién comprar una licencia | **(leída)** |
| **F5-TTS** | Pesos CC BY-NC 4.0 | **(leída)** |
| **Microsoft** (Azure, Edge) | "You may not use the AI services, or data from the AI services, to create, train, or improve… any other AI service"; para voces personales, "based only on their own voice" | **(snippet)** / **(leída)** |
| **Google Cloud TTS** | §17(b): no usar la salida para "substitute, replace, or circumvent the use of a Google Model" | **(leída)** |
| **ElevenLabs** | Prohíbe usar la salida "to develop, train, fine-tune, or improve any AI model", y clonar "the voice… of any living individual" sin consentimiento | **(leída)** |
