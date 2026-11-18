# Inglés: LibriVox, los Lectores de Hi-Fi TTS y LJSpeech

> Investigación del 2026-11-17. Qué fuentes en inglés tienen licencia CC0 o de dominio público y calidad de narrador, por qué los 10 lectores de Hi-Fi TTS son el mejor filtro de calidad, qué pasa con LJSpeech y qué se descarta. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**, **medido**.

---

## 1. Resumen

* **La mejor fuente es LibriVox, bajada directamente de Archive.org**, no los datasets derivados. Archive.org marca cada ítem con `publicdomain/mark/1.0` o `publicdomain/zero/1.0` en el campo `licenseurl` **(leída**, API `archive.org/metadata/<id>`**)**.
* **NVIDIA ya filtró la calidad**: los 10 lectores de Hi-Fi TTS se eligieron entre 250 de LibriVox por SNR ≥ 32–40 dB y ancho de banda ≥ 13 kHz, **y NVIDIA les pidió consentimiento escrito para TTS** **(leída**, arXiv 2104.01497**)**. El dataset Hi-Fi TTS es CC BY 4.0, pero el audio original de esos lectores en LibriVox es dominio público.
* **LJSpeech es dominio público** ("There are no restrictions on its use") y ya trae la transcripción alineada, pero está a 22 kHz y sale de MP3 de 128 kbps **(leída)**.
* **En el banco, las voces de LibriVox en inglés dieron las notas UTMOS más altas** (4.0–4.5) **medido** ([10](10-pruebas-en-gpu.md)).

---

## 2. Los 10 Lectores de Hi-Fi TTS

Tabla 2 del paper **(leída)**. "clean" es el subconjunto con SNR ≥ 40 dB; "other", ≥ 32 dB.

| ID LibriVox | Lector | Género | Horas clean / other |
| :--- | :--- | :--- | :--- |
| 92 | **Cori Samuel** | F | 27.3 / – |
| 6097 | Phil Benson | M | 30.1 / 3.4 |
| 9017 | **John Van Stan** | M | 58.0 / – |
| 6670 | Mike Pelton | M | – / 17.7 |
| 6671 | Tony Oliva | M | – / 24.1 |
| 8051 | **Maria Kasper** | F | – / 30.4 |
| 9136 | Helen Taylor | F | – / 24.3 |
| 11614 | Sylviamb | F | – / 22.2 |
| 11697 | Celine Major | F | – / 26.8 |
| 12787 | LikeManyWaters | F | – / 27.3 |

No se sabe si ese consentimiento alcanza a terceros **(no verificado)**.

### 2.1 Probados en el banco

| Lector | Clip (URL verificada por API) | Licencia del ítem | Resultado **medido** |
| :--- | :--- | :--- | :--- |
| **Cori Samuel** | `https://archive.org/download/frankenstein_cs_librivox/frankenstein_01_shelley.mp3` (prefacio, 204–216 s) | `publicdomain/zero/1.0` | **La mejor**: UTMOS 4.47/4.47, SIM 0.987/0.981, WER 0. Voz clara de audiolibro, probablemente británica |
| **John Van Stan** | `https://archive.org/download/frankenstein_4_2010_librivox/frankenstein4_01_shelley.mp3` (77.6–89.4 s) | `publicdomain/mark/1.0` | UTMOS 3.98/4.49, SIM 0.955/0.949. Voz grave y pausada (F0 ~100 Hz, ref a 123 ppm): storytelling y documental |
| Maria Kasper | `https://archive.org/download/instructionslightkeepers_1404_librivox/instructionstolightkeepers_01_uslb.mp3` (260.5–269.5 s) | `publicdomain/mark/1.0` | UTMOS 3.67/4.10, SIM 0.971/0.983. Lee no ficción técnica: tono explicativo para tutoriales |

Phil Benson no se probó: su único clip verificado es poesía (*Song of Myself*), y para narrar conviene prosa, como *The Man in the Queue*.

---

## 3. Otras Fuentes CC0 o de Dominio Público

| Fuente | Licencia | Calidad | Nota | Marca |
| :--- | :--- | :--- | :--- | :--- |
| **LJSpeech 1.1** (Linda Johnson) | "public domain in the US… There are no restrictions on its use" | 22 050 Hz mono, 13 100 clips de 1–10 s, 24 h, 2.6 GB. Algo monótona | `metadata.csv` revisado a mano, listo para CosyVoice. Es tan conocida en TTS que "suena a modelo" (**no verificado**). La ficha de HF dice "You agree to not attempt to determine the identity of speakers", en **conflicto** con la página original, que la nombra | **(leída)** |
| Common Voice (en) | CC0 + no identificar a los hablantes + no re-hospedar | Crowdsourcing casero, muchos acentos | No es voz de narrador | **(snippet)** |
| GLOBE / GLOBE_V2 | `cc0-1.0` | V2 a 44.1 kHz por **sobremuestreo** (no es banda real), con "filtering and enhancement" | Derivado de Common Voice: arrastra la cláusula de no identificar | **(leída)** |
| VOA Learning English | Dominio público, "with credit to learningenglish.voanews.com" | Estudio de radio | Locución lenta a propósito (~2/3 de la velocidad normal): no sirve para reels. En 2026 VOA opera de forma reducida **(snippet)** | **(leída)** |
| NASA | "generally are not subject to copyright", con crédito | Muy variable | Desaconsejado: prohíbe usar los "personality traits" de empleados en material comercial | **(leída)** |
| Library of Congress, National Archives | Obras federales sin copyright (17 U.S.C. §105) | Baja fidelidad histórica | Clonar a un presidente es el caso típico de suplantación: **no usar** | **no verificado** |
| Kyutai voice-donations y Voice-Zero | CC0 | Ver [05](05-donaciones-cc0-kyutai-y-voice-zero.md) | Las mejores opciones listas para usar | **(leída)** |

---

## 4. Descartados en Inglés

| Fuente | Licencia citada | Motivo |
| :--- | :--- | :--- |
| Hi-Fi TTS (SLR 109) | "CC BY 4.0" **(leída)** | CC BY. Usar el audio de LibriVox |
| HiFiTTS-2 | CC BY 4.0; "LibriVox audiobooks are not redistributed" **(leída)** | CC BY en metadatos y alineaciones |
| LibriTTS (SLR 60) y LibriTTS-R (SLR 141) | CC BY 4.0 **(leída)** | CC BY |
| VCTK 0.92 | "Creative Commons Attribution 4.0" **(leída)** | CC BY. 110 hablantes a 48 kHz, acentos británicos |
| Expresso y EARS (Meta) | CC BY-NC 4.0 **(leída)** | No comercial, aunque EARS es de cámara anecoica |
| Jenny (Dioco) | Licencia propia: atribución obligatoria como "Jenny (Dioco)" **(leída)** | No es CC0; acento irlandés |
| Elise | "mit", con acceso deshabilitado por un "DMCA Takedown notice" **(leída)** | Origen no documentado y retirado por DMCA |
| Emilia / Emilia-YODAS | NC (Emilia) y CC BY (YODAS); "copyright remains with the original owners" **(leída)** | Audio de YouTube de terceros. **Conflicto**: el metadato de HF dice `cc-by-4.0` |

---

## 5. Receta

Es igual que en español ([03](03-librivox-en-espanol.md) §4), con dos detalles:

* `curl https://archive.org/metadata/<id>` lista los archivos de un ítem y su `licenseurl`. Muchos ítems publican también un `*_spectrogram.png` por capítulo, útil para ver la banda antes de bajar **(leída)**.
* Los lectores a veces cambian palabras del texto: "when a reader modifies the reference text while reading" (paper de Hi-Fi TTS) **(leída)**. Por eso la transcripción tiene que salir del audio, no del libro.
