# Donaciones CC0: Kyutai `tts-voices` y Voice-Zero

> Investigación del 2026-11-17. Las dos colecciones curadas de referencias listas para clonar: las donaciones de voz de Kyutai, que son CC0 **con consentimiento explícito para clonar** e incluyen voces en español, y Voice-Zero, una selección CC0 de LibriVox procesada. Qué hay en cada una, cómo se clasificaron y qué se aprendió. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**, **medido**.

---

## 1. Resumen

* **Kyutai `voice-donations/` es la única fuente encontrada que junta las dos cosas**: licencia CC0 y consentimiento del hablante para la clonación. "Voices of volunteers submitted through our Unmute Voice Donation Project, licensed as CC0. The Voice Donation project ran from June 2025 to February 2026 and collected 228 voices that passed verification, out of a total 374 submissions" **(leída)**.
* **El protocolo de donación incluye leer una frase de consentimiento**, que se oye en los clips: "I consent to my voice being used for voice cloning" (Hannah, Nick, Enrique…) y, en español, "doy mi consentimiento para que mi voz se utilice para la clonación de voz" (`spanish-limaperu`) **medido**.
* **Hay voces en español**: 218 clips con nombre, y entre ellos `Alejandro_espanol_latino`, `Andrea_(Spanish)`, `Enrique_(Spanish)`, `spanish-limaperu`, `Yesid`, `John_Triguero`, `Richard_cuban` y otros **(leída**, listado de la API de HF**)**. No traen metadatos de idioma: se clasificaron con whisper **medido**.
* **La calidad es casera**: son clips de exactamente 10 s a 24 kHz, a veces cortados a mitad de palabra. En el banco clonaron bien (SIM 0.96–0.98, WER ≤ 0.10), con UTMOS menor que LibriVox **medido** ([10](10-pruebas-en-gpu.md)).
* **Voice-Zero** ([OwenTyme/voice-zero](https://github.com/OwenTyme/voice-zero)) son 155 clips CC0 de LibriVox, todos en inglés, recortados a 7–12 s y **fuertemente procesados** (RNNoise, resíntesis con Kanade, Resemble Enhance) **(leída)**. El clip de Cori Samuel resultó ser **el aviso de LibriVox**, no narración **medido**.

---

## 2. Kyutai `tts-voices`

Repo: [huggingface.co/kyutai/tts-voices](https://huggingface.co/kyutai/tts-voices). Las voces son para Pocket TTS y Kyutai TTS 1.6B, pero los WAV sirven para cualquier clonador **(leída)**.

### 2.1 Licencia por Carpeta

| Carpeta | Contenido | Licencia | ¿Uso comercial? |
| :--- | :--- | :--- | :--- |
| `voice-donations/` | 228 voces de voluntarios (Unmute Voice Donation) | **CC0** | **Sí** |
| `voice-zero/` | 4 voces de Voice-Zero (LibriVox) | **CC0** | Sí |
| `unmute-prod-website/` | Voces de Unmute.sh: "The others are our own recordings and you may use them as CC0", salvo `degaulle-2.wav` (1940), `ex04_…` (Expresso, NC) y `p329_022.wav` (VCTK, CC BY) | CC0 con excepciones | Sí, salvo las tres excepciones |
| `vctk/`, `cml-tts/fr/`, `alba-mackenna/` | VCTK, CML-TTS francés, actriz Alba MacKenna | CC BY 4.0 | Con atribución (fuera del criterio) |
| `expresso/`, `ears/` | Datasets de Meta | **CC BY-NC 4.0**: "Non-commercial use only" | **No** |

Cada voz trae `X.wav` (original), `X_enhanced.wav` (limpiado con ai-coustics) y embeddings `.safetensors` para Kyutai TTS **(leída)**.

### 2.2 Clasificación de las Donaciones **medido**

Se bajaron 38 donaciones (las de nombre hispano y algunas en inglés) y se pasaron por whisper `medium` (`clasificar.py`): idioma detectado, confianza (`avg_logprob`), nivel y piso de ruido.

| Donación | Idioma detectado (p) | logprob | Piso (dB) | Qué dice / observación |
| :--- | :--- | :--- | :--- | :--- |
| **Yesid** | es (0.99) | −0.19 | −76 | "Incluye una torre de cruce y un campanario. El disco de Relay vendió más de 6 millones de copias como sencillo." Dos frases completas |
| **John_Triguero** | es (1.00) | −0.19 | −62 | Empieza a mitad de frase ("…explosión también dejó al ejército…") |
| **Andrea** | es (0.96) | −0.31 | −63 | Tono motivacional; corta a mitad de frase al final |
| Chujus | es (0.98) | −0.35 | −73 | "…es una delicia poder clonar…" |
| Enrique_(Spanish) | es (1.00) | −0.12 | −50 | Texto sobre Zaragoza: posiblemente peninsular (**no verificado**) |
| Richard_cuban | es (0.86) | −0.25 | −86 | Cubano, según el nombre |
| Andrea_(Spanish) | es (0.99) | −0.53 | −60 | Menor confianza |
| spanish-limaperu | es (0.99) | −0.30 | −64 | Solo la frase de consentimiento (7.9 s) |
| hielos_1 / hielos_2 | es (0.26) | −0.5 | −66 | Mezcla español e inglés |
| Alejandro_espanol_latino | **en** (0.96) | −0.43 | −62 | A pesar del nombre, lee en inglés |
| Esteban_Aguirre_Arias | la (0.48) | −0.91 | −93 | Ininteligible |
| Gonzalo, Jaspino, Rafaelpazv | en | — | −92 a −180 | Saturados (RMS −8 a −11 dB) o con silencio digital |
| **Hannah** | en (1.00) | −0.18 | −67 | Incluye la frase de consentimiento y "Hey, this is Hannah. Okay, bye." |
| **Nick** | en (1.00) | −0.25 | −64 | Frases completas tras el consentimiento |

Para el banco se eligieron **Yesid, John_Triguero y Andrea** (español) y **Hannah y Nick** (inglés), por idioma claro, confianza alta y nivel sano. Los clips se usaron enteros, con la transcripción de whisper, porque Kyutai los publica como referencias de 10 s listas para usar.

### 2.3 Cómo Bajar una Donación

```bash
curl -L -o Yesid.wav https://huggingface.co/kyutai/tts-voices/resolve/main/voice-donations/Yesid.wav
# Listar todas (nombres con paréntesis van con %28 %29 en la URL):
curl -s https://huggingface.co/api/models/kyutai/tts-voices/tree/main/voice-donations
```

---

## 3. Voice-Zero

| Dato | Valor | Marca |
| :--- | :--- | :--- |
| Qué es | "A collection of open source compatible voice samples mostly from public domain and Creative Commons works", pensada para Chatterbox y Pocket TTS | **(leída)** |
| Licencia | "The voices directory … will *always* hold CC0-licensed samples". La API de GitHub devuelve `NOASSERTION` porque `LICENSE.md` no es un texto SPDX | **(leída)** |
| Contenido | 155 clips FLAC en `voices/`, de 7 a 12 s, con lector, acento estimado y fuente en `voices/README.md`. Muchos vienen de *Celebration of Dialects and Accents* (acentos confiables). Además, `voices-emotion/` tiene variantes emocionales **sintéticas** generadas con Chatterbox | **(leída)** |
| Idioma | Solo inglés (acentos de EE. UU., Reino Unido, Australia, y hablantes no nativos de alemán, neerlandés, húngaro…) | **(leída)** |
| Procesado | Recorte a 8–11 s; denoise de Audacity; RNNoise (VAD 99 %); cambios de tempo para "fix overly slow or fast speakers"; normalización a −8 dB; **resíntesis con Kanade** para quitar reverberación; *upscale* a 44 kHz con Resemble Enhance | **(leída)** |

### 3.1 Dos Hallazgos del Banco **medido**

1. **El clip `cori_samuel.flac` es el aviso de LibriVox**: "All LibriVox recordings are in the public domain. For more information, or to volunteer, please visit librivox dot org" (de *Black Beauty*, versión 2, pista 1). Whisper `medium` lo devolvió **vacío**; `large-v3-turbo` sí lo transcribió. Hasta un pack curado puede traer una referencia que no es narración.
2. **El procesado de Voice-Zero no cambió lo medido**: los clones del clip procesado dieron UTMOS 4.38/4.46 y SIM 0.988/0.984, y los del clip crudo de Cori Samuel en LibriVox (otro libro), 4.47/4.47 y 0.987/0.981. La similitud entre los dos clips de Cori fue 0.973, como corresponde a la misma persona. La comparación no es limpia, porque los textos son distintos, pero no muestra la caída de similitud que la investigación previa atribuye al denoise ([voicestudio-narracion/11](../voicestudio-narracion/11-audio-de-referencia.md) §3). **Conflicto** parcial: con un solo caso, no alcanza para concluir.

Para usar Voice-Zero, conviene preferir los clips de *Celebration of Dialects and Accents*, que tienen el acento confirmado, y escuchar el clip antes de usarlo.

---

## 4. Comparación

| Criterio | Kyutai voice-donations | Voice-Zero | LibriVox directo |
| :--- | :--- | :--- | :--- |
| Licencia | CC0 | CC0 | Dominio público (EE. UU.) |
| Consentimiento para clonar | **Sí, explícito** | No (lectores de LibriVox) | No |
| Español | **Sí** (~10 voces) | No | Sí (565 libros) |
| Calidad | Casera, 24 kHz, 10 s fijos | Procesada, 44 kHz (sobremuestreada) | Audiolibro, 44.1 kHz |
| Transcripción | No (hay que transcribir) | No | No (hay texto fuente) |
| Corte | A veces a mitad de palabra | Frases completas | Lo eliges tú |
| Lugar en el catálogo | `yesid`, `andrea`, `hannah`, `nick` | — | `karen-savage`, `mpinedag`, `cori-samuel`, `john-van-stan` |
