# Comparativa de Motores y Licencias

> Investigación del 2026-11-15. Los seis motores (los cuatro de VoiceStudio y los dos que ya usa `narration/`) lado a lado: licencia, recursos medidos en la RTX 4060, comportamiento con el español, control expresivo y qué conviene para cada tipo de video. Índice en [README.md](README.md). Marcas: **(leída)**, **medido** ([13](13-pruebas-en-gpu.md)), **no verificado**, **conflicto**.

---

## 1. Licencias

| Motor | Código | Pesos | Uso en videos monetizados | Fuente |
| :--- | :--- | :--- | :--- | :--- |
| Qwen3-TTS Base | Apache-2.0 | Apache-2.0 | Sí | `narration/README.md` |
| Chatterbox Multilingual | MIT | MIT | Sí (marca de agua PerTh incorporada). **Sin mantenimiento desde agosto de 2026** | README **(leída)** |
| **VoxCPM2** | Apache-2.0 | **Apache-2.0** | **Sí** | Card y technical report **(leída)** |
| **CosyVoice 3** | Apache-2.0 | Apache-2.0 en metadatos; la card dice "for academic purposes only" | **Probable, con duda**: dos pedidos de aclaración sin respuesta | **(leída)**: **conflicto** |
| **IndexTTS 2.5** | bilibili Model Use License | Igual | **Riesgoso**: salidas = obra derivada, prohíbe entrenar otros modelos con ellas, ley china, *disclaimer* ambiguo | LICENSE, DISCLAIMER **(leída)** |
| **OmniVoice** | Apache-2.0 | **CC-BY-NC** + Higgs Audio 2 + Llama 3 | **No**: el autor lo confirma para un youtuber monetizado | Card, issue #235 **(leída)** |
| VoiceStudio (app) | AGPL-3.0 | — | La app sí; los modelos según su licencia. **La app exige aceptar la licencia de OmniVoice antes de generar** (`403 model_licence_required`) | README **(leída)**, **medido** ([14](14-replicacion-de-voicestudio.md)) |

Esto no es asesoría legal ([01](01-metodo-y-fuentes.md) §5).

---

## 2. Recursos Medidos (RTX 4060 Laptop 8 GB, WSL2)

| Motor | Venv / Python / torch | VRAM pico | Primera carga | RTF mediano (frases de 2–8 s) | Salida |
| :--- | :--- | :--- | :--- | :--- | :--- |
| OmniVoice | `.venv-omnivoice` / 3.12 / 2.14.1 | **2.22 GiB** | 48 s | 1.23 | 24 kHz |
| CosyVoice 3 | repo / 3.10 / 2.14.1 | **3.50 GiB** | **12 s** | **1.20** | 24 kHz |
| IndexTTS 2.5 | repo / 3.11 / 2.8.0 | 5.69 GiB (6.79 con `emo_text`) | 29 s | 1.97 (10.8 con `emo_text`) | 22.05 kHz |
| VoxCPM2 | `.venv-voxcpm` / 3.12 / 2.14.1 | 5.75 GiB | 102 s (incluye la descarga) | 1.81 | **48 kHz** |
| Qwen3-TTS 0.6B / 1.7B | `.venv-qwen` | ~1.15 GiB por bloque en lote | — | Ver `narration/README.md` §6 | 24 kHz |

Todos caben en 8 GB **de a uno**. El RTF en frases cortas está dominado por el costo fijo: en párrafos largos baja. IndexTTS con el Qwen de emoción desborda a la RAM compartida (16× más lento).

---

## 3. Español: Resultados del Banco de Pruebas

15 frases comunes × 2 semillas. "Exactas" = whisper transcribió sin diferencias; los 4 casos con números nunca cuentan como exactos porque whisper los escribe en dígitos, así que **el máximo es 26 de 30**.

| Motor | Exactas | Palabras/s (ref. 3.3) | Lo peor medido |
| :--- | :--- | :--- | :--- |
| CosyVoice 3 | **26 / 30** | 2.87 | Homógrafo inestable; instrucción en español leída 1 de 10 |
| VoxCPM2 | 25 / 30 | 3.19 | "Apera el WhatsApp" (1 de 2); lee `<strong>`; en Hi-Fi lee la instrucción |
| IndexTTS 2.5 | 23 / 30 | **2.02** (no copia la referencia) | **Lee "—" como "menos"**; números en dígitos mal; lee todas las etiquetas |
| OmniVoice | 20 / 30 | 3.09 | **Omite el tramo tras `…`**; siglas mal; `[pause]` y `<strong>` rompen la salida |

Detalle por caso en [13](13-pruebas-en-gpu.md) §4.

---

## 4. Control Expresivo

| Capacidad | Qwen Base | Chatterbox | OmniVoice | VoxCPM2 | IndexTTS 2.5 | CosyVoice 3 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Emoción por referencia | Sí | Sí | Sí | Sí (Hi-Fi) | Sí | Sí (zero-shot) |
| Emoción por parámetro | — | `exaggeration`, `cfg_weight` | — | Instrucción `(…)` en inglés | **Vector de 8 emociones, graduable** | Instrucción en inglés (`instruct2`) |
| Risa / suspiro inline | — | — | `[laughter]`, `[sigh]` | Altera el texto | Se leen | `[laughter]`, `[sigh]` |
| Respiración inline | — | — | Se lee | Altera el texto | Se lee | **`[breath]`** |
| Énfasis inline | — | — | Rompe | Se lee | Se lee | **`<strong>`** |
| Velocidad | `atempo` | Indirecta | `speed` | Instrucción | `duration_factor` | `speed` |
| Susurro | Referencia | Referencia | Diseño `whisper` (sin clonar) | Instrucción (efecto medible en F0) | Referencia | No funcionó (VoiceStudio) |

Columnas de Qwen y Chatterbox desde `narration/`; el resto **medido**, salvo donde se cita.

---

## 5. Recomendación por Tipo de Video

| Video | Motor sugerido | Por qué |
| :--- | :--- | :--- |
| **Demos y tutoriales** | VoxCPM2 Hi-Fi o CosyVoice 3 zero-shot | Lectura exacta de siglas y números; 48 kHz en VoxCPM2; ritmo copiado de una referencia `experta` a 140–160 ppm |
| **Reels** | CosyVoice 3 o VoxCPM2 con referencia `energica` | Rápidos de cargar (Cosy) y precisos; la energía sale de la referencia |
| **Storytelling** | IndexTTS 2.5 (vector de emoción) si la licencia no es problema; si lo es, CosyVoice 3 con `[breath]` e `instruct2` en inglés | Emoción graduable; respiraciones |
| **Publicidad** | VoxCPM2 Hi-Fi con referencia `energica` | Licencia clara y 48 kHz |
| Uso personal o pruebas | OmniVoice | El más liviano (2.2 GiB), con `[laughter]` y `[sigh]` |

Antes de elegir un motor por defecto hay que repetir el banco con **la voz real del usuario** ([README](README.md#preguntas-abiertas)).
