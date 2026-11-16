# Guion y Pronunciación en Español

> Investigación del 2026-11-15. Cómo escribir el texto que recibe el motor: formato, acentuación, homógrafos, números, siglas, extranjerismos y nombres, y qué marcas funcionan en cada motor. Complementa las reglas ya medidas con Qwen en [formato-guion.md](../../../narration/docs/formato-guion.md). Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**, **medido** ([13](13-pruebas-en-gpu.md)).

---

## 1. Principios de los Proveedores, Aplicados a Modelos Abiertos

Los proveedores comerciales trabajan en **tres capas**: la voz o referencia fija el rango posible, una instrucción corta de actuación ajusta el estilo y el texto puntuado lleva el detalle. "El parámetro más importante es la voz que eliges" (ElevenLabs v3 **(leída)**, B).

| Principio | Fuente | Cómo aplica aquí |
| :--- | :--- | :--- |
| **El texto debe contener la emoción** ("alineación semántica") | Hume Octave **(leída)**, ElevenLabs **(leída)** | Un texto enojado sale enojado aunque no haya instrucción |
| **Una emoción por bloque**; partir el turno cuando cambia | Gemini 3.8 TTS **(leída)**; VoiceStudio `[emotion:]` **(leída)** | `tts.py` ya parte por párrafos: una emoción por párrafo |
| **Solo etiquetas documentadas**; las inventadas se leen o aplanan la voz | LiveKit/Gemini, Orpheus, Fish, VoiceStudio **(leída)** | Ver la tabla de §5 por motor |
| Las notas de estilo deben **amplificar, no amortiguar** ("quiet", "flat", "no rush" aplanan) | LiveKit (pruebas propias, A/B) **(leída)** | Instrucciones de VoxCPM2 y CosyVoice: "warm and sincere" y no "quiet" |
| Etiquetas en **inglés** aunque el texto sea en otro idioma | Gemini 3.8 **(leída)** | Coincide con lo medido en VoxCPM2 ([04](04-voxcpm2.md) §4) |
| Generar varias tomas y elegir | ElevenLabs **(leída)**; regla 24 local | `--reintentos` |

---

## 2. Acentuación y Homógrafos

* Los modelos sin G2P explícito deciden la sílaba tónica **por la tilde**. Medido localmente con Qwen ("Hoy termino el guion" → "terminó"), y en esta investigación:

| Motor | "Hoy termino el informe" (sin tilde, presente) | Resultado |
| :--- | :--- | :--- |
| OmniVoice | Whisper oyó "terminó" en 1 de 2 | **medido** |
| VoxCPM2 | Whisper oyó "terminó" en 2 de 2 | **medido** |

* Whisper también tiene sesgo hacia "terminó" después de "Hoy", así que estos casos se confirman escuchando ([13](13-pruebas-en-gpu.md) §6).
* Pares a cuidar: término/termino/terminó, público/publico/publicó, práctica/practica/practicó, sé/se, más/mas, tú/tu, él/el.
* **No existe IPA ni `<phoneme>` para español en ningún motor abierto revisado**: solo pinyin (chino) y CMU (inglés) en OmniVoice, VoxCPM2, IndexTTS 2.5 y CosyVoice 3 **(leída)**. La herramienta sigue siendo el **respelling** (reglas 14–16 locales).
* En comerciales: Azure acepta `<phoneme alphabet="ipa">` en es-ES (indirecto, **(snippet)**); ElevenLabs v3/v4 lee IPA entre barras con 80–90 % de consistencia **(snippet)**.

---

## 3. Números, Siglas, Extranjerismos y Nombres

| Elemento | Qwen (local) | OmniVoice | VoxCPM2 | Regla |
| :--- | :--- | :--- | :--- | :--- |
| Números en dígitos ("25", "1500 pesos") | Sin confirmar | Bien | Bien | **En letras igual**: CosyVoice normaliza todo lo no chino **en inglés** ("25" → "twenty-five") e IndexTTS no normaliza español sin `nemo_text_processing` ([05](05-indextts-2-5.md), [06](06-cosyvoice-3.md)) |
| Siglas (QR, IMC) | Mal sin deletrear | **Mal** ("query", "IMSS") | Bien | **Deletrear**: "cu erre", "i eme ce" |
| Extranjerismos (WhatsApp, Zoom, stock) | Respelling | Bien | 1 de 2 mal ("Apera el WhatsApp") | Respelling ("guasap", "estok") si falla; en OmniVoice, VoxCPM2 e IndexTTS hay CMU inline para inglés (`[W AA1 T S AE2 P]`), sin probar |
| Marcas inventadas | "Clinikái" | Sin probar | Sin probar | Respelling con tilde en la sílaba tónica |
| Mayúsculas | Sin efecto | Sin efecto audible | Sin efecto audible | No usarlas: en ElevenLabs, Hume y Gemini sí dan énfasis, **en estos motores no** (**conflicto por motor**) |

Todo medido en [13](13-pruebas-en-gpu.md) salvo la columna de Qwen, que viene de [formato-guion.md](../../../narration/docs/formato-guion.md).

**IndexTTS 2.5** y **CosyVoice 3** leyeron bien las siglas sin deletrear. Con los números en dígitos, IndexTTS falló ("mil cimientos pesos", "500 pesos") y CosyVoice, sin normalizador, acertó. La regla de escribir los números en letras sigue siendo la única que funciona en los seis motores.

---

## 4. Signos y Pausas

| Signo | Qwen (medido local) | OmniVoice | VoxCPM2 |
| :--- | :--- | :--- | :--- |
| `,` | 0.30 s | 0.16–0.34 s | 0.20–0.46 s |
| `…` | 0.52 s, la más estable | **Riesgo: omitió el tramo siguiente** en 2 de 2 ("despacio… y no había nadie") | 0.24–0.72 s, sin omisiones |
| `—` | 0.42 s | Sin omisiones en "sin prisa — y guarda" | Sin omisiones |
| Pausa larga | `[pausa N]` de `tts.py` (silencio real) | Igual: **nunca pasar `[pause]` al modelo** (rompe la generación) | Igual |

* **Punto vs coma**: LiveKit (Gemini) reporta que los fragmentos separados por punto suenan entrecortados; las reglas locales 6 y 21 prefieren el punto en Qwen. **Conflicto** sin resolver con medición; se mantiene la regla local para Qwen y se recomienda escuchar en los motores nuevos.
* Mantener `…` en 1–2 por bloque (LiveKit, regla local 5).

---

## 5. Marcas por Motor (Qué Escribir y Qué No)

| Marca | Qwen Base | Chatterbox | OmniVoice | VoxCPM2 | IndexTTS 2.5 | CosyVoice 3 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `[laughter]` | Se lee | Se lee (no verificado) | **Funciona** | No se lee | **Se lee** ("Lotter") | **Funciona** |
| `[sigh]` | Se lee | — | **Funciona** | Altera el inicio | **Se lee** ("SAI") | **Funciona** |
| `[breath]` | "Braids" | — | **Se lee** | Altera palabras vecinas | **Se lee** | **Funciona** |
| `<strong>…</strong>` | Se lee | — | **Rompe la salida** | **Se lee** ("strong") | **Se lee** | **Funciona** |
| `[pause]` | "pause" | — | **Rompe la salida** | No se lee | **Se lee** | **Se lee** ("pausa") |
| `—` (raya) | 0.42 s | — | Sin problema | Sin problema | **Se lee "menos"** | Sin problema |
| `(instrucción)` al inicio | Se lee | — | Se lee | **Funciona** (inglés > español; en Hi-Fi se lee) | No aplica (vector) | Usa `instruct2` aparte |

Columnas de Qwen desde [formato-guion.md](../../../narration/docs/formato-guion.md); el resto **medido** en [13](13-pruebas-en-gpu.md).

**Regla general:** `tts.py` debería **quitar o rechazar** toda marca que el motor elegido no soporte antes de enviarle el texto. VoiceStudio hace lo contrario (pasa el texto tal cual y avisa en la UI) **(leída, `expressive-speech.md`)**; por eso sus usuarios reportan etiquetas leídas.

---

## 6. Técnica de Locutor Traducida a Texto TTS

| Marca de locutor | En el guion TTS |
| :--- | :--- |
| `/` pausa corta | `,` |
| `//` pausa larga | `.` o `…` (no en OmniVoice a mitad de oración), o `[pausa N]` |
| Subrayado (énfasis) | Llevar la palabra al **final del grupo** sin dejarla última del párrafo (regla 22), aislarla con `…` antes o usar una escindida ("Lo que cambia todo es…") |
| ↗ (sube) | `¿…?` en preguntas absolutas; en enumeraciones, el penúltimo antes de "y" |
| ↘ (baja) | Cerrar con `.` |
| [sonrisa], [calma] | Cambiar la referencia o la instrucción (VoxCPM2, CosyVoice, IndexTTS) |

La notación de [guiones/](../../../narration/docs/guiones/README.md) (barras, flechas) sirve para grabar referencias y **nunca** pasa al texto TTS (regla 1).
