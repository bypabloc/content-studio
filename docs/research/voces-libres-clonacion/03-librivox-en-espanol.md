# LibriVox en Español: la Fuente Grande de Dominio Público

> Investigación del 2026-11-17. Por qué LibriVox es la única fuente grande de voz en español de calidad de audiolibro con licencia de dominio público, qué lectores conviene probar, cómo bajar y recortar un capítulo, y por qué los datasets derivados de LibriVox llevan otra licencia. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**, **medido**.

---

## 1. Resumen

* **LibriVox es dominio público**: "all our recordings are public domain… anyone can use all our recordings however they wish (even to sell them)" **(leída)**. La garantía es para EE. UU.: "maybe in your country as well".
* **Hay 565 audiolibros en español** en la colección `librivoxaudio` de Archive.org **medido** (consulta `advancedsearch`).
* **El perfil del lector no dice su país**: el acento hay que escucharlo **(leída)**.
* **Los datasets derivados (MLS, CML-TTS, M-AILABS, CSS10) ponen su licencia a la compilación**: la segmentación, la alineación y los metadatos. El MP3 original de LibriVox sigue siendo dominio público. Para CC0 o dominio público estricto, **se baja el capítulo original y el recorte y la transcripción se hacen aparte** **(leída)**.
* **No hay consentimiento para clonar**: ningún lector aceptó explícitamente que se clone su voz ([02](02-derechos-copyright-y-voz.md)).

---

## 2. Lectores Candidatos

Los datos de libros y lectores salen de la API de LibriVox **medido**. El audio se midió con ffprobe y astats sobre 60 s del capítulo 1. En las pruebas del banco **medido** ([10](10-pruebas-en-gpu.md)), "ref" es el tramo de 9–12 s elegido.

| Lector (ID) | Libro solo (ID LibriVox) | Audio de la fuente | Acento | Resultado en el banco |
| :--- | :--- | :--- | :--- | :--- |
| **Karen Savage** (103), 141 proyectos | *Angelina*, de Rafael Delgado, novela mexicana (1946) | 44.1 kHz mono 128 kbps; ruido de fondo de una grabación de 2011 (piso de la ref −54 dB) | **No verificado**. M-AILABS dice que "karen" es mexicana **(leída)**, pero no se confirmó que sea la misma persona | **La mejor en español**: SIM 0.993/0.962, UTMOS 3.78/3.66, WER 0 |
| **mpinedag** (3796), 131 proyectos | *Compendio de Historia de la América Central* (21985) | 44.1 kHz estéreo VBR ~109 kbps; piso ≈ −77 dB en la fuente, −53 dB en la ref | **No verificado**. Elige autores centroamericanos (Gómez Carrillo, Milla): es una inferencia | SIM 0.985/0.985, UTMOS 3.49/3.13, WER 0; voz grave (F0 ~90 Hz) |
| **Epachuko** (12367), 177 proyectos | *Crimen y castigo* (15136) | 44.1 kHz estéreo VBR ~111 kbps; piso ≈ −70 dB | **No verificado** | SIM 0.991/0.982, UTMOS 3.11/2.60, WER 0. **Ojo**: es una traducción, que puede tener derechos del traductor fuera de EE. UU. |
| Victor Villarraza (8882), 116 proyectos | *Aventuras de Sherlock Holmes* (17047) | El audio más limpio medido (≈ −82 dB) | **Probablemente rioplatense**: M-AILABS dice que "victor" es argentino, y además grabó una *Antología de autores argentinos* | No se probó: no es neutro |
| "Tux" (lector de CSS10) | Galdós: *La Batalla de los Arapiles*, *Gerona*, *Cádiz*… | — | **Probablemente peninsular** | No se probó |
| Consuelo Aponte (19733), Meribau (19049), GatoLunar (19413) | Secciones de *Cuentos populares en Chile* (21132), *Historia natural de los fantasmas… de Colombia* (21296) y *Periquillo Sarniento* (20191) | Proyectos colectivos, sin medir | **No verificado** | No se probó |

Enlaces:

* Karen Savage: [librivox.org/angelina-por-rafael-delgado](https://librivox.org/angelina-por-rafael-delgado/) · MP3 del capítulo 1: `https://archive.org/download/angelina_1109_librivox/angelina_01_delgado.mp3` · texto: Gutenberg #16082.
* mpinedag: [librivox.org/compendio-de-historia-de-la-america-central-…](https://librivox.org/compendio-de-historia-de-la-america-central-by-agustin-gomez-carrillo/) · MP3: `https://archive.org/download/comphistoriacam_2511_librivox/comphistoriacam_01_gomez.mp3` · texto: HathiTrust `txu.059173018500584`.
* Epachuko: [librivox.org/crimen-y-castigo-…](https://librivox.org/crimen-y-castigo-by-fyodor-dostoyevsky/) · MP3: `https://archive.org/download/crimen_y_castigo_2105_librivox/crimenycastigo_01_dostoyevsky.mp3`.

Para encontrar más lectores, el endpoint que usa la propia página del lector devuelve sus proyectos (requiere el encabezado `X-Requested-With: XMLHttpRequest`) **medido**:

```
https://librivox.org/reader/get_results?primary_key=<ID>&search_category=reader&search_page=1&search_order=alpha&project_type=solo
```

La API de audiolibros devuelve los lectores por sección y la `listen_url` de cada MP3 **medido**:

```
https://librivox.org/api/feed/audiobooks/?title=^<título>&extended=1&format=json
```

---

## 3. Otras Fuentes en Español con CC0 o Dominio Público

| Fuente | Licencia | Por qué sirve poco | Marca |
| :--- | :--- | :--- | :--- |
| **Common Voice (es)** | CC0-1.0, más la condición de no identificar a los hablantes y no re-hospedar el dataset. Desde octubre de 2025 solo se distribuye por Mozilla Data Collective | Micrófonos caseros y frases de ~5 s. Hay que bajar un TAR de decenas de GB para filtrar por `accents` y `client_id` | **(snippet)** para la ficha; **(leída)** para el aviso de HF |
| **VOA en español** | "All text, audio and video material produced exclusively by the Voice of America is in the public domain", salvo AFP, AP y Reuters | Son locutores periodistas **identificables**, con derecho a la voz, y el audio suele traer cortinas musicales | **(leída)** |
| CDC en español | "Most of the information… is in the public domain", salvo lo producido por contratistas | Los podcasts suelen ser de contratistas: hay que verificar caso por caso | **(leída)** |
| Lingua Libre (Wikimedia) | El grabador elige CC0, CC BY o CC BY-SA. **Por defecto, CC BY-SA 4.0** | Son palabras sueltas, no narración | **(snippet)** |
| CSS10 (es) | **Conflicto**: el repo muestra Apache-2.0, un espejo de HF dice CC0 y Kaggle no se pudo leer | Mejor bajar el original de LibriVox | **(leída)** / **(snippet)** |
| M-AILABS es_ES | La envoltura es tipo BSD ("including any commercial use"); el audio, "recorded by the LibriVox project and is also in the public domain" | 16 kHz, peor que el original a 44.1 kHz | **(leída)** |

---

## 4. Cómo Bajar y Recortar un Capítulo

Es la receta que automatizan `tmp/research-voces/elegir.py` (banco) y `narration/voces.py` (catálogo):

1. **Bajar el capítulo en VBR o 128 kbps**, no la versión `_64kb`.
2. **Saltar el preámbulo**: los primeros 20–30 s dicen "Esta es una grabación de LibriVox…" con otra entonación.
3. **Transcribir con marcas de tiempo por palabra** (whisper `medium`, `word_timestamps=True`) y armar frases que terminen en `.`, `?` o `!`.
4. **Elegir de 8.5 a 12 s de frases completas y consecutivas**, con huecos de menos de 0.7 s, sin diálogo (`"`, `«`, `—`) y sin la primera frase de la ventana. Con los segmentos de whisper, en cambio, los tramos empezaban a mitad de frase ("los acontecimientos notables…") **medido**.
5. **Recortar sin procesar**: mono, frecuencia de muestreo original, PCM de 24 bits, 0.25 s de margen a cada lado:

```bash
ffmpeg -ss 66.99 -t 11.66 -i angelina_01_delgado.mp3 -ac 1 -c:a pcm_s24le ref.wav
```

6. **Corregir la transcripción contra el texto fuente** (Gutenberg o HathiTrust), con cuidado con la ortografía antigua ("Méjico") y las abreviaturas que el lector expande. En esta investigación no se pudo cotejar, porque Gutenberg rechazó la descarga automática ([01](01-metodo-y-fuentes.md) §4).

---

## 5. Descartados en Español

| Fuente | Licencia | Nota |
| :--- | :--- | :--- |
| OpenSLR 61 (Argentina), 71 (Chile), 72 (Colombia), 73 (Perú), 74 (Puerto Rico), 75 (Venezuela) | CC BY-SA 4.0 **(leída** para 61, 71, 72 y 73**)** | Google crowdsourced, con calidad de estudio. Sería la mejor fuente latinoamericana si se aceptara CC BY-SA |
| TEDx Spanish (SLR 67) | CC BY-NC-ND 4.0 **(leída)** | NC y ND |
| Multilingual LibriSpeech (SLR 94) | CC BY 4.0 **(leída)** | Envoltura de LibriVox: usar el original |
| CML-TTS (SLR 146) | CC BY 4.0 **(leída)** | Ídem, 24 kHz |
| CIEMPIESS | CC BY-SA 4.0 **(snippet)** | Mexicano, radio de la UNAM |
| DIMEx100 | Solo académico; el uso comercial requiere convenio con la UNAM **(snippet)** | 100 hablantes mexicanos de estudio |
| JFSpeech | Sin licencia declarada **(leída)** | Lectora "Joyfull" de LibriVox: su original sí es PD |
| F5-Spanish (jpgallegoar) | CC BY-NC 4.0 **(snippet)** | Modelo, no dataset |

La tabla completa de descartes, incluidas las fuentes en inglés y las voces sintéticas, está en [07](07-descartados.md).
