# Recepción de la Comunidad

> Investigación del 2026-11-15. Qué gusta y qué se odia de los motores de VoiceStudio y de la app, con el nivel de evidencia de cada opinión. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**; evidencia **A** (estudio con método), **B** (dato de proveedor con muestra), **C** (anécdota o comentario).

**Limitaciones:** Reddit devolvió 403 en todas las consultas y el buscador no indexó hilos de r/LocalLLaMA ni r/TextToSpeech sobre estos motores; Hacker News no tiene discusiones útiles; YouTube y X no se revisaron. La evidencia sale de issues y discusiones de GitHub y Hugging Face, de blogs y de un benchmark de proveedor (Soniqo). Úsese como señal, no como prueba: lo medido en esta máquina está en [13](13-pruebas-en-gpu.md).

---

## 1. Resumen

* **OmniVoice**: el más elogiado por calidad multilingüe y velocidad; el más criticado por la **licencia no comercial** (youtubers que se fueron) y por **omitir o repetir palabras**.
* **VoxCPM2**: gusta por 48 kHz, Apache-2.0 y el diseño de voz; se critica la memoria, que la voz varíe con el texto y las alucinaciones en frases muy cortas.
* **IndexTTS 2.5**: el único con emoción graduable; usuarios chinos dicen que **retrocede frente a 2.0** en emoción y timbre. Nadie confirmó todavía el español latino.
* **CosyVoice 3**: buena similitud de hablante y `[breath]`; críticas fuertes por **repeticiones e inestabilidad** frente a CosyVoice 2, y por la instalación.
* **VoiceStudio (la app)**: casi no hay reseñas independientes; las que hay (andrew.ooo, computingforgeeks, remio) se apoyan en su documentación (B/C).

---

## 2. Benchmarks de Terceros en Español

| Fuente | Conjunto | Resultado | Nivel |
| :--- | :--- | :--- | :--- |
| Soniqo, 2026-07 | FLEURS **es_419** (latinoamericano), 10 referencias | OmniVoice (int8): coseno 0.758, WER 9.9 % · VoxCPM2: 0.641, 5.8 % · Chatterbox: 0.708, 6.9 % · Qwen3-TTS 1.7B: 0.710, 11.1 % · Fish S2 Pro: 0.633, 6.8 % | B (proveedor con método publicado y muestra pequeña) **(leída)** |
| Paper de OmniVoice | MiniMax-24, español | OmniVoice WER 1.026 / SIM 0.804 | B (autores) **(leída)** |
| README de VoxCPM2 | MiniMax-MLS, español | VoxCPM2 WER 1.438 / SIM 83.1; Qwen3-TTS 1.126 / 81.4 | B (autores) **(leída)** |
| README de IndexTTS 2.5 | CV3-Eval, español | IndexTTS 2.5: 3.75 / 76.4 · CosyVoice3-0.5B: 4.04 / **78.85** · Qwen3-TTS: **2.87** / 73.2 · OmniVoice: 3.52 / 74.1 · VoxCPM2: 5.49 / 74.7 | B (proveedor interesado) **(leída)** |

Lectura conjunta: **no hay un ganador estable**. Cada tabla favorece al que la publica. Lo consistente: OmniVoice y CosyVoice clonan bien el timbre; VoxCPM2 es más inteligible en es_419 pero menos parecido a la voz; Qwen3-TTS tiene buen WER en español pero clona menos el timbre.

---

## 3. Por Motor

### 3.1 OmniVoice

| Gusta | Se odia | Nivel |
| :--- | :--- | :--- |
| "the multilingual cloning quality is excellent"; en checo, "clearly the best open model we have tried" (#258) | **Licencia CC-BY-NC**: "we do not hold the rights to grant any commercial license" (autor a un youtuber monetizado, #235); otros se fueron (#258, #275) | C **(leída)** |
| "IMO, the best TTS out there" (guiones en inglés de 15–17 min, #116) | Se traga finales de palabra antes de coma o punto en español (#116) | C **(leída)** |
| Muy rápido (RTF 0.025–0.09 en H100) | Omite partes del texto (#253, también en una RTX 3050 de 8 GB); repite palabras (#134) | C **(leída)**; la omisión se **reprodujo** aquí ([13](13-pruebas-en-gpu.md)) |
| Ecosistema: audio.cpp, GGUF | VRAM que crece con cada llamada (#199); OOM en 8 GB sin `ref_text` (#282) | C **(leída)** |

### 3.2 VoxCPM2

| Gusta | Se odia | Nivel |
| :--- | :--- | :--- |
| 48 kHz, Apache-2.0, diseño de voz, clonación de "very good quality" (#321) | La voz cambia un poco según el texto incluso en Hi-Fi con cfg 3 (#231) | C **(leída)** |
| Corre en una RTX 2060 de 6 GB (#357) | Alucina sílabas en frases de 1–2 palabras (#357); audio extra al final con `*-()` en español (#216) | C **(leída)** |
| | Sin control de pausas (#276); acentos de diseño poco fiables (#285); memoria y caídas con la UI (#261, #300) | C **(leída)** |

### 3.3 IndexTTS 2.5

| Gusta | Se odia | Nivel |
| :--- | :--- | :--- |
| Control de emoción graduado, el único entre los motores de VoiceStudio | "为什么感觉情感色彩上没有2.0好" (el color emocional no es tan bueno como en 2.0), varios "+1" (#759) | C **(leída)** |
| Cross-lingual y velocidad (RTF 0.21 en 4090, B) | "情绪控制和音色还原上开了2.0的倒车" (retrocede en emoción y timbre), "sensación muy marcada de IA, voz que se quiebra" (#781) | C **(leída)** |
| | Pedido de español latino neutro sin respuesta (#805); la última frase de un párrafo inventa contenido con segmentos de 120 tokens (#775) | C **(leída)** |

### 3.4 CosyVoice 3

| Gusta | Se odia | Nivel |
| :--- | :--- | :--- |
| `[breath]` como la etiqueta de respiración más directa (VoiceStudio) | "Fun-CosyVoice3-0.5B的效果简直就是噩梦" (el resultado es una pesadilla) por repeticiones (#1703, 29 comentarios) | C **(leída)** |
| Mejor SS en español en CV3-Eval | Japonés y ruso salen en chino (#1675, #1790) | B / C **(leída)** |
| Baja VRAM, ecosistema activo (vLLM, cosyvoice.cpp) | Instalación difícil (HF #1, #18); "garbled, garbage audio… switched to F5-TTS" con ONNX (HF #10) | C **(leída)** |

### 3.5 Qwen3-TTS y Chatterbox (los motores actuales)

| Motor | Comunidad | Nivel |
| :--- | :--- | :--- |
| Qwen3-TTS | Exige fijar semilla, recortar la referencia a ~10 s y ajustar parámetros; Chatterbox aceptó 41 s sin tocar nada (archy.net) | C **(snippet)** |
| Chatterbox | Mejor UTMOS en es_419 (3.37, Soniqo, B). **Retirado y sin mantenimiento desde agosto de 2026** según su README | B / **(leída)** |

---

## 4. VoiceStudio como App

* El repo muestra ~111k estrellas; no se encontró discusión independiente proporcional a esa cifra (**no verificado**).
* Reseñas encontradas: andrew.ooo (B, basada en la doc), computingforgeeks (guía de instalación), remio y aiadoptionagency.com (C). Ver [herramientas/](herramientas/README.md) §7 de cada archivo.
* Los issues muestran mucho mantenimiento activo (cientos de PR y regresiones corregidas: semillas por trozo #3730, masterización con eco #986, limitador #3412), lo que indica uso real.

---

## 5. Lista: Lo que Más se Valora

| Valorado | Motor |
| :--- | :--- |
| Calidad multilingüe y velocidad | OmniVoice |
| Licencia comercial clara | VoxCPM2 |
| Emoción graduable | IndexTTS 2.5 |
| Respiración y similitud de timbre | CosyVoice 3 |

## 6. Lista: Lo que Más se Critica

| Criticado | Motor |
| :--- | :--- |
| Licencia no comercial | OmniVoice |
| Palabras omitidas o repetidas | OmniVoice, CosyVoice 3 |
| Regresión de emoción frente a la versión anterior | IndexTTS 2.5 |
| Instalación difícil | CosyVoice 3, IndexTTS |
| Memoria alta | VoxCPM2 |
