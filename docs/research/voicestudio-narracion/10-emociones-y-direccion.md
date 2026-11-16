# Emociones, Sensaciones y Dirección de Actuación

> Investigación del 2026-11-15. Cómo pedir una emoción o una sensación (alegría, urgencia, calma, suspenso, susurro, sonrisa, respiración) en cada motor, con prompts que funcionaron medidos en la RTX 4060, recetas por tipo de video y antipatrones. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**, **medido** ([13](13-pruebas-en-gpu.md)); evidencia A/B/C.

---

## 1. Las Cuatro Palancas

| Palanca | Qué controla | Motores | Fiabilidad |
| :--- | :--- | :--- | :--- |
| **1. La referencia** | Timbre, ritmo, energía, emoción, acento y sala | Todos | **La más fiable** (todos los proveedores y VoiceStudio: "the most reliable expressive control") **(leída)** |
| 2. El texto | Léxico emocional, signos, longitud de frase | Todos | Alta: "use expressive input text to produce more expressive speech" (Hume) **(leída)** |
| 3. Parámetro o instrucción | Emoción sobre la misma referencia | VoxCPM2, IndexTTS 2.5, CosyVoice 3, Chatterbox | Media: varía por voz y por semilla **medido** |
| 4. Etiquetas inline | Risa, suspiro, respiración, énfasis puntual | OmniVoice (`[laughter]`, `[sigh]`), CosyVoice 3 (todas) | Depende del motor ([08](08-guion-y-pronunciacion.md) §5) |

Orden de uso: **referencia → texto → instrucción → etiqueta**. Una emoción que no está en el texto ni en la referencia suena forzada (Hume, Orpheus, LiveKit) **(leída)**.

---

## 2. Prompts por Motor

### 2.1 VoxCPM2 (instrucción al inicio, modo controlable)

* Solo con `reference_wav_path` (sin `prompt_text`): en modo Hi-Fi la instrucción **se lee** **medido**.
* **En inglés**: las instrucciones en español cambiaron menos la salida **medido**.
* Fórmula del cookbook **(leída)**: identidad + textura + escena, breve, sin espacio antes del texto.

| Intención | Instrucción | Medido |
| :--- | :--- | :--- |
| Entusiasta (reel, anuncio) | `(cheerful and energetic)` | 4.0 → 3.2 s; F0 mediana 250 Hz (1 semilla) |
| Triste | `(sad and slow)` | Sin cambio claro de duración |
| Urgente | `(urgent, speaking fast)` | Sin cambio claro de duración |
| Susurro | `(whispering)` | Rango de F0 de 25 a 5.4 st (más plano) |
| Calma | `(calm and confident)` | 4.0 → 3.5 s |
| Tutorial | `(warm, confident, slightly faster)` | Sin probar (fórmula del cookbook) |

Generar 1–3 tomas: "adherence varies" **(leída)**.

### 2.2 IndexTTS 2.5 (vector de 8 emociones)

Orden `[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]`; normalizar como la WebUI (sesgo por emoción y suma ≤ 0.8) y `emo_alpha` ≤ 0.6 **(leída)**.

| Intención | Vector | Efecto medido |
| :--- | :--- | :--- |
| Alegría | `[0.8, 0, 0, 0, 0, 0, 0, 0]` | Algo más aguda |
| Tristeza | `[0, 0, 0.8, 0, 0, 0, 0, 0]` | **1.5× más lenta** |
| Enojo | `[0, 0.8, 0, 0, 0, 0, 0, 0]` | F0 +45 Hz; perdió la primera palabra |
| Miedo / tensión | `[0, 0, 0, 0.8, 0, 0, 0, 0]` | Más rápida y aguda |
| Sorpresa | `[0, 0, 0, 0, 0, 0, 0.8, 0]` | Pausas de 1 s |
| Calma | `[0, 0, 0, 0, 0, 0, 0, 0.8]` | Más grave |
| Mezcla (suspenso) | `[0, 0, 0, 0.4, 0, 0.3, 0, 0]` | Sin probar |

`emo_text` funciona en español en los casos simples, pero cuesta 1.1 GiB y es 5× más lento en 8 GB **medido**: preferir el vector. Un `emo_audio_prompt` (clip de emoción de 5–8 s) toma la emoción de otra grabación sin cambiar el timbre **(leída)**.

### 2.3 CosyVoice 3 (`inference_instruct2`)

Formato: `You are a helpful assistant. <instrucción en inglés><|endofprompt|>` **(leída)**.

| Intención | Instrucción | Medido |
| :--- | :--- | :--- |
| Tristeza | `Please speak in a sad and slow tone.` | 5.2–5.8 s vs 3.5–3.8 s; F0 más plana |
| Urgencia | `Please speak in a urgent, speaking fast tone.` | Hasta 4.2 palabras/s |
| Alegría | `Please speak in a cheerful and energetic tone.` | Pausas más largas, sin cambio claro de F0 |
| Susurro | `Please say it whispering.` | Sin cambio claro (VoiceStudio: los estilos no se siguen, las emociones sí) |
| Volumen alto / bajo | `Please say a sentence as loudly as possible.` / `in a very soft voice.` | Oficiales, sin probar **(leída)** |

`instruct2` **ignora la entrega de la referencia**: la voz puede parecerse menos al clon **(leída)**. Instrucciones cortas: las largas se leen (#1903) **(leída)**; en español se leyó 1 de 10 **medido**.

### 2.4 Chatterbox (ya en `narration/`)

| Intención | `exaggeration` | `cfg_weight` | Fuente |
| :--- | :--- | :--- | :--- |
| Neutro (por defecto) | 0.5 | 0.5 | README **(leída)** |
| Expresivo o dramático | ≥ 0.7 | ~0.3 (compensa la aceleración) | README **(leída)** |
| Referencia rápida | — | ~0.3 | README **(leída)** |
| Referencia en otro idioma que el texto | — | 0 (evita filtrar el acento) | README **(leída)** |

Por encima de 1.5 aparecen artefactos (C, **(snippet)**). Los estilos actuales de `tts.py` usan 0.3–0.6 / 0.4–0.6.

### 2.5 Qwen3-TTS Base y OmniVoice

Sin control de emoción en modo clonación: **una referencia por emoción** es la única palanca ([11](11-audio-de-referencia.md) §6). OmniVoice agrega `[laughter]` y `[sigh]` y, sin referencia, el diseño `whisper`. El flujo oficial de Qwen "Voice Design then Clone" (diseñar una voz con emoción y usarla como referencia) confirma que el Base copia la emoción de la referencia, pero no clona el timbre propio **(leída)**.

---

## 3. Sensaciones Específicas

| Sensación | Cómo lograrla | Motores |
| :--- | :--- | :--- |
| **Sonrisa audible** | Grabar la referencia sonriendo de verdad: los oyentes la detectan incluso susurrada (Tartter 1980, Quené; A **(snippet)**) | Todos |
| **Susurro** | Referencia `intima` (voz baja y cercana) antes que susurro real, que pierde timbre; o `(whispering)` en VoxCPM2 | VoxCPM2, referencia |
| **Respiración** | `[breath]` en CosyVoice 3; en los demás, grabarla en la referencia y apagar la limpieza de silencios (receta de VoiceStudio) **(leída)** | CosyVoice 3 |
| **Risa** | `[laughter]` en OmniVoice y CosyVoice 3; con el texto pidiéndola ("me dijo que sí… [laughter]") | OmniVoice, CosyVoice 3 |
| **Suspenso** | `…` antes del dato clave (no en OmniVoice), frases cortas, referencia `dramatica`; IndexTTS con miedo + melancolía | Todos |
| **Urgencia** | Frases cortas, imperativos, `¡…!`; VoxCPM2 o CosyVoice con instrucción en inglés; IndexTTS con miedo | Todos |
| **Calma y confianza** | Frases más largas con subordinadas, cierres en `.`; referencia `estable` o `suave` | Todos |
| **Énfasis en una palabra** | `<strong>` en CosyVoice 3; en los demás, posición focal ([09](09-entonacion-y-ritmo.md) §3) | CosyVoice 3 |

---

## 4. Recetas por Tipo de Video

| Video | Referencia | Texto | Motor y ajuste |
| :--- | :--- | :--- | :--- |
| **Tutorial / demo** | `experta` grabada a 140–160 ppm | Imperativos claros, una acción por oración, siglas deletreadas | VoxCPM2 Hi-Fi o CosyVoice zero-shot |
| **Reel** | `energica` o `amistosa` | Gancho de 4–5 palabras, `[pausa 0.5]`, frases de 8–12 palabras | CosyVoice zero-shot; VoxCPM2 `(cheerful and energetic)` sobre `neutral` |
| **Storytelling** | `dramatica` o `intima` | `…` para suspenso (no en OmniVoice), frases cortas en el clímax, una emoción por párrafo | IndexTTS con vector por párrafo; CosyVoice con `[breath]` |
| **Publicidad** | `energica` | Beneficio al final del grupo, CTA con `¡…!` | VoxCPM2 Hi-Fi; Chatterbox `exaggeration` 0.7 / `cfg_weight` 0.3 |

---

## 5. Antipatrones

| Antipatrón | Qué pasa | Fuente |
| :--- | :--- | :--- |
| Etiquetas de ElevenLabs (`[excited]`, `[whispers]`) en modelos abiertos | Se leen o rompen la salida | VoiceStudio **(leída)**, **medido** |
| Instrucción en Hi-Fi de VoxCPM2 | Se lee en voz alta | **medido** |
| Instrucciones largas o en español en CosyVoice | Se leen | #1903 **(leída)**, **medido** |
| Notas que amortiguan ("quiet", "flat", "no rush") | Aplanan la voz | LiveKit **(leída)** |
| Emoción que no calza con el texto | Suena forzada | Hume, Orpheus **(leída)** |
| Referencia sobreactuada | Todo hereda la sobreactuación | ElevenLabs, guía local |
| Cambiar de emoción a mitad de una oración | Rompe la entonación | VoiceStudio `[emotion:]` **(leída)** |
| `emo_alpha` alto con `emo_text` en IndexTTS | Menos natural | README IndexTTS **(leída)** |
| `exaggeration` alto sin bajar `cfg_weight` (Chatterbox) | Se acelera | README Chatterbox **(leída)** |
