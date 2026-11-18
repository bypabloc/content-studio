# Voces que Piden Mención (CC BY, CC BY-SA y Licencias Propias)

> Investigación del 2026-11-18 (ampliación pedida por el usuario). Qué significa que una voz "pida mención", cómo se cumple al publicar un video narrado con una voz clonada, qué fuentes en español e inglés tienen licencia de uso comercial con atribución, y cómo se sumaron al catálogo. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**, **medido**. **No es asesoría legal.**

---

## 0. Qué Significa "Mención"

> **Mención** (o *atribución*) es la condición de una licencia que obliga a **dar crédito al autor** cada vez que se publica algo hecho con su obra. Se permite usar la voz (incluso con fines comerciales), pero hay que decir **de quién es, de dónde sale y con qué licencia**, y avisar que se modificó. En este proyecto, "voz que pide mención" es una voz del catálogo cuya licencia es **CC BY**, **CC BY-SA** o una licencia propia con crédito obligatorio (Jenny). El texto exacto que hay que publicar está en el campo `atribucion` de [narration/voces/catalogo.json](../../../narration/voces/catalogo.json). `tts.py --voz` lo imprime en cada corrida y lo guarda en el `.json` de la toma (`voces[].mencion`).

Lo opuesto son las voces **CC0 o de dominio público** ([03](03-librivox-en-espanol.md)–[05](05-donaciones-cc0-kyutai-y-voice-zero.md)): esas no exigen crédito, aunque darlo no cuesta nada.

**Mención no es permiso de la persona.** La licencia CC la otorga quien publicó el dataset (Google, la Universidad de Edimburgo, Kyutai), no el hablante. CC BY 4.0, §2(b)(1): "Moral rights… nor are publicity, privacy, and/or other similar personality rights" **(leída)**. El derecho a la voz sigue como en [02](02-derechos-copyright-y-voz.md).

---

## 1. Qué Exige la Licencia (CC BY 4.0, §3(a))

Texto de la licencia **(leída**, [legalcode](https://creativecommons.org/licenses/by/4.0/legalcode.en)**)**:

> "If You Share the Licensed Material (including in modified form), You must: A. retain… i. identification of the creator(s)… ii. a copyright notice; iii. a notice that refers to this Public License; iv. a notice that refers to the disclaimer of warranties; v. a URI or hyperlink to the Licensed Material…; B. indicate if You modified the Licensed Material…; and C. indicate the Licensed Material is licensed under this Public License, and include the text of, or the URI or hyperlink to, this Public License."
>
> §3(a)(2): "You may satisfy the conditions… in any reasonable manner based on the medium, means, and context… For example, it may be reasonable to satisfy the conditions by providing a URI or hyperlink to a resource that includes the required information."

| Elemento | Qué poner en el video | Marca |
| :--- | :--- | :--- |
| Creador | El nombre que pide el licenciante (en VCTK, los tres autores y CSTR) | **(leída)** |
| Aviso de copyright | Solo si el licenciante lo da (VCTK: "© 2019") | **(leída)** |
| Licencia | "CC BY 4.0" con el enlace | **(leída)** |
| URI | Enlace o DOI del dataset | **(leída)** |
| Modificación | "Usada solo como referencia para generar una voz sintética" | **(leída)** |
| Título | Opcional en 4.0; **obligatorio en 3.0 y anteriores** | **(leída**, wiki de CC**)** |

La práctica recomendada por Creative Commons es **TASL**: *Title, Author, Source, License* **(leída**, [wiki](https://wiki.creativecommons.org/wiki/Best_practices_for_attribution)**)**. Para audio y video recomienda poner el crédito "in the description text of the audio/video" y, cuando se pueda, también en el propio video.

### 1.1 Dónde Ponerla

| Plataforma | Dónde | Marca |
| :--- | :--- | :--- |
| YouTube | **Descripción** (el texto `atribucion` completo) y, si se puede, una línea en los créditos finales | **(leída)** recomendación de CC; aplicación a YouTube: inferencia |
| Shorts, TikTok, Reels | Un caption corto ("Voz sintética · ref.: VCTK p329, CC BY 4.0 · créditos: <url>") y el texto completo en una **página de créditos** (link in bio). §3(a)(2) lo admite | **(leída)** |
| Archivo de audio suelto | Metadatos (comentario ID3) y la página de créditos | Inferencia |

### 1.2 ¿La Narración Clonada es "Material Adaptado"?

* Una salida zero-shot de CosyVoice **no contiene los sonidos de la grabación**: imita el timbre. En EE. UU., 17 U.S.C. §114(b) dice que el derecho sobre una grabación no alcanza a "another sound recording that consists entirely of an independent fixation of other sounds, even though such sounds imitate or simulate those in the copyrighted sound recording" **(leída)**. Lo más probable es que la narración **no** sea material adaptado y que, en rigor, la condición de mención ni se active.
* **Pero no hay jurisprudencia**, y en la UE existen derechos conexos del intérprete (**no verificado**). La guía de CC sobre IA dice que, para las salidas, "providing attribution to the CC-licensed work tied to the particular model output with a link to the source is ideal" **(snippet)**.
* **Si el clip original aparece en el video** (por ejemplo, para mostrar "la voz de referencia"), eso **sí** es material adaptado: "Adapted Material is always produced where the Licensed Material is synched in timed relation with a moving image" **(leída)**.

**Regla del proyecto: dar siempre la mención, como si la narración fuera una adaptación.** Cuesta una línea, sigue la recomendación de CC y, de paso, avisa que la voz es sintética.

### 1.3 Compartir Igual (CC BY-SA)

* CC BY-SA 4.0 §3(b): si se comparte material adaptado, "The Adapter's License You apply must be a Creative Commons license with the same License Elements" **(leída)**.
* Si alguien sostuviera que la narración es una adaptación, el video tendría que publicarse con CC BY-SA, que permite a cualquiera reutilizarlo comercialmente. TikTok e Instagram no ofrecen licencias CC (**no verificado**).
* **Conflicto** entre los dos informes de esta investigación: el de español concluye que el ShareAlike "casi seguro no alcanza al audio que genera CosyVoice"; el de inglés recomienda **no usar fuentes BY-SA para contenido comercial**. Las dos cosas son compatibles: el riesgo es bajo, pero existe. Por eso las voces BY-SA del catálogo **imprimen un aviso aparte** en `tts.py`.

### 1.4 Licencias Propias

**Jenny (Dioco)** **(leída)**: "Attribution is required in software/websites/projects/interfaces (including voice interfaces) that generate audio in response to user action using this dataset… the voice must be referred to as "Jenny", and where at all practical, "Jenny (Dioco)". **Attribution is not required when distributing the generated clips** (although welcome). Commercial use is permitted."

Para un video (un clip distribuido) la mención no es obligatoria, pero el catálogo la incluye igual.

---

## 2. Fuentes en Español

| Fuente | Licencia | Calidad | Consentimiento | Veredicto |
| :--- | :--- | :--- | :--- | :--- |
| **Google crowdsourced Latin American Spanish** (OpenSLR 61, 71–75) | **CC BY-SA 4.0** **(leída)** | Neumann KM 184, cabina acústica portátil, 48 kHz/16 bit; piso de −72 a −90 dBFS, banda completa **(leída**, paper LREC 2020; **medido)** | "volunteers", "specifically constructed with text-to-speech applications in mind", IDs anónimos. **Sin consentimiento explícito para clonar** **(leída)** | **La mejor**. Clips de 3–10 s con 40–60 % de silencio: hay que unir 2–3 |
| CML-TTS español (SLR 146) | CC BY 4.0 **(leída)** | 24 kHz, pero banda útil de ~8–10 kHz (viene de MP3); texto con puntuación **(medido)** | Lectores de LibriVox | Segunda opción (por ejemplo, el lector 13325, "Mariohdezch") |
| Multilingual LibriSpeech (SLR 94) | CC BY 4.0 **(leída)** | 16 kHz, sin puntuación; un lector satura a 0 dBFS **(medido)** | Lectores de LibriVox | Mejor CML-TTS, que tiene los mismos lectores |
| Sharvard (Edimburgo) | CC BY 3.0 **(leída)** | 48 kHz, frases de 2 s | No se menciona | Marginal: peninsular, hay que unir 4–5 frases |
| CIEMPIESS | CC BY-SA 4.0 **(leída)** | Podcasts de radio, 16 kHz | Invitados de radio identificables | **No** |
| MediaSpeech (SLR 108) | CC BY 4.0 **(leída)** | Recortes de YouTube | Terceros | **No** |
| `Kukedlc/arg-spanish-tts` | Reetiquetado CC BY **(leída)** | — | — | **Conflicto**: deriva de SLR 61 (BY-SA); el reetiquetado no quita el ShareAlike |

### 2.1 Cómo Bajar Solo un Clip de OpenSLR

Los zips pesan ~0.8 GB, pero los espejos aceptan `Range` ("Accept-Ranges: bytes", **(leída)**). Basta con leer el índice central del zip y solo los WAV pedidos: listar un zip de 860 MB tomó 3.6 s **(medido)**. `narration/voces.py` lo hace con `ZipRemoto` (stdlib: `zipfile` sobre un archivo HTTP con `Range`), y el catálogo describe la voz como `partes: [{url, miembro}]`.

### 2.2 Unir Clips Cortos

Los clips de OpenSLR tienen un clic o una respiración al final que frena `silenceremove`. Con ese filtro, la base de Colombia quedó de 20.3 s con tres pausas de 1.4–2.6 s **(medido)**. `voces.tramo_voz()` toma, en cambio, desde el fin del silencio inicial hasta el primer silencio de 0.8 s o más (método del agente de investigación, `silencedetect` a −40 dB). Las bases quedaron de 13.6 s (Colombia, 3 clips), 11.0 s (Perú, 3) y 10.2 s (Venezuela, 2), sin pausas de 1 s o más **(medido)**.

---

## 3. Fuentes en Inglés

| Fuente | Licencia | Calidad | Mención pedida (literal) | Veredicto |
| :--- | :--- | :--- | :--- | :--- |
| **VCTK 0.92** (CSTR, Edimburgo) | CC BY 4.0 **(leída)** | 110 hablantes, cámara hemianecoica, 48 kHz | "Christophe Veaux, Junichi Yamagishi, Kirsten MacDonald, "CSTR VCTK Corpus: English Multi-speaker Corpus for CSTR Voice Cloning Toolkit", The Centre for Speech Technology Research (CSTR), University of Edinburgh" **(leída)** | **Recomendada**. Clips sueltos de 10–13 s vía Kyutai (`vctk/pXXX_023.wav`) |
| Kyutai `unmute-prod-website/p329_022.wav` | CC BY 4.0 (VCTK) **(leída)** | 48 kHz, 8.4 s | La de VCTK | **Recomendada**: Kyutai la usa como voz de producción |
| **Kyutai `alba-mackenna/`** | "Characters voice-acted by Alba MacKenna… Released under the CC BY 4.0 licence" **(leída)** | Actriz de voz, 48 kHz, ~10 s por personaje | No pide un texto; se usa TASL | Usable. **Evitar `a-moment-by`**: "Private recordings requested by Kinder World" → **conflicto** de derechos |
| **Jenny (Dioco)** | Propia, comercial **(leída)** | ~30 h, 48 kHz **estéreo**, clips sin recortar | "Jenny (Dioco)" | Usable |
| Alba speech corpus (Edimburgo) | CC BY 4.0; "Any use derogatory to the voice talent is prohibited" **(leída)** | Actriz profesional, escocesa, 48 kHz | "Valentini-Botinhao, Cassia; Yamagishi, Junichi. (2019). Alba speech corpus…" | Frases de ~2.8 s: hay que unir varias. No se sumó |
| Hi-Fi TTS, LibriTTS-R | CC BY 4.0 **(leída)** | Lectores de LibriVox | Ver [04](04-ingles-librivox-ljspeech-y-otros.md) | El audio original de LibriVox es dominio público: no hace falta la versión CC BY |

Del clip "announcer" de Alba MacKenna, whisper transcribió frases sueltas de videojuego ("New record. No contest. Online. Player 1. Player 2…"), y de "casual", respuestas cortas. Se eligió **"merchant"**, que es habla más continua **(medido)**.

---

## 4. Voces Sumadas al Catálogo

| Voz | Idioma | Licencia | Fuente | Base | Aprobación ([10](10-pruebas-en-gpu.md) §7.1) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `colombia-m` | es | CC BY-SA 4.0 | OpenSLR 72, hablante com_05223 | 3 clips unidos, 13.6 s | **12/12** |
| `peru-f` | es | CC BY-SA 4.0 | OpenSLR 73, hablante pef_06136 | 3 clips, 11.0 s | **12/12** |
| `venezuela-f` | es | CC BY-SA 4.0 | OpenSLR 75, hablante vef_02484 | 2 clips, 10.2 s; el piso más limpio (−87 dB) | **12/12** (1.ª ronda) |
| `vctk-p329` | en | CC BY 4.0 | VCTK p329 (vía Kyutai) | 8.4 s | 9/12 |
| `vctk-p345` | en | CC BY 4.0 | VCTK p345 (vía Kyutai) | 11.6 s | **12/12** |
| `alba-mackenna` | en | CC BY 4.0 | Kyutai, personaje "merchant" | 10 s | 10/12 |
| `jenny` | en | Jenny (propia, con mención) | Dioco, `sample/24.wav` | 11.1 s, pasado a mono | 4/12 |

Las transcripciones salen de los TSV de OpenSLR y de VCTK y de `24.txt` de Jenny, con la puntuación que falta agregada a mano. Se verificaron con whisper `large-v3-turbo`, que solo difirió en detalles propios de whisper ("aprieta" en lugar de "apriete", "flat" en lugar de "flapped") **(medido)**. Ninguna de estas voces tiene consentimiento explícito para clonar (`consentimiento: false`), así que `tts.py` muestra los dos avisos.

**Entran a `--voz` 4 voces con mención**: las 3 de OpenSLR y VCTK p345. Las otras 3 quedan en el catálogo, deshabilitadas en el menú con el motivo.

---

## 5. Qué Hace `tts.py` con una Voz que Pide Mención

```
$ python cli.py narration tts --modelo cosyvoice3 --voz vctk-p329 --idioma en --texto "..."
Aviso: la voz vctk-p329 (CSTR VCTK Corpus 0.92, hablante p329 (vía Kyutai tts-voices)) tiene licencia CC BY 4.0, pero su dueño no dio permiso para clonarla…
MENCIÓN OBLIGATORIA (CC BY 4.0): pon este crédito en la descripción del video. Queda en el .json.
  Voice reference: speaker p329 from "CSTR VCTK Corpus" (v0.92) by Christophe Veaux, …
```

Con una voz BY-SA, además:

```
Aviso: licencia "compartir igual" (BY-SA). No pongas el clip original en el video, y si alguien considera la narración una adaptación, tendría que publicarse con la misma licencia.
```

En el `.json` de la toma:

```json
"voces": [{"voz": "vctk-p329", "licencia": "CC BY 4.0", "fuente": "…", "consentimiento": false, "mencion": "Voice reference: …"}]
```

El menú de `cli.py` marca estas voces con "pide mención", y `voces.py --listar` muestra el texto completo.
