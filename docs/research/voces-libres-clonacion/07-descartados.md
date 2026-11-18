# Fuentes Descartadas y Por Qué

> Investigación del 2026-11-17. Todo lo que se evaluó y no cumple el criterio "solo CC0 o dominio público", en una sola tabla, con la licencia citada y la nota útil por si el criterio cambia. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**.

---

## 1. Regla Práctica

**Los datasets derivados de LibriVox licencian la compilación, no el audio.** MLS, CML-TTS, Hi-Fi TTS, LibriTTS, M-AILABS, CSS10 y JFSpeech ponen su licencia (CC BY, BSD, Apache) a la segmentación, la alineación y los metadatos. El MP3 original del mismo lector en LibriVox sigue siendo dominio público ([03](03-librivox-en-espanol.md), [04](04-ingles-librivox-ljspeech-y-otros.md)). Por eso varios descartes tienen un "plan B" en la última columna.

---

## 2. Tabla

| Fuente | Idioma | Licencia citada | Motivo | Plan B dentro del criterio |
| :--- | :--- | :--- | :--- | :--- |
| OpenSLR 61, 71–75 (Google crowdsourced) | es (AR, CL, CO, PE, PR, VE) | CC BY-SA 4.0 **(leída** 61, 71–73; **snippet** 74–75**)** | Atribución y share-alike | Ninguno: no salen de LibriVox |
| TEDx Spanish (SLR 67) | es | CC BY-NC-ND 4.0 **(leída)** | NC y ND | — |
| CIEMPIESS | es (MX) | CC BY-SA 4.0 **(snippet)** | Share-alike | — |
| DIMEx100 | es (MX) | Solo académico **(snippet)** | Uso comercial con convenio | — |
| Multilingual LibriSpeech (SLR 94) | es, en… | CC BY 4.0 **(leída)** | Atribución | Bajar el capítulo de LibriVox |
| CML-TTS (SLR 146) | es… | CC BY 4.0 **(leída)** | Atribución | Ídem |
| M-AILABS es_ES | es | Tipo BSD **(leída)** | No es CC0 (pide conservar el aviso) | Ídem (audio PD según su página) |
| CSS10 (es) | es | **Conflicto**: Apache-2.0 / CC0 / CC BY-SA según el espejo | Licencia incierta | Ídem |
| JFSpeech | es | Sin licencia **(leída)** | Desconocida | Ídem |
| LibriVox Spanish (LDC2020S01) | es | Licencia LDC **no verificado** | Distribución no libre | Ídem |
| Hi-Fi TTS (SLR 109), HiFiTTS-2 | en | CC BY 4.0 **(leída)** | Atribución | Ídem: los 10 lectores están en LibriVox |
| LibriTTS (SLR 60), LibriTTS-R (SLR 141) | en | CC BY 4.0 **(leída)** | Atribución | Ídem |
| VCTK 0.92 | en (UK) | CC BY 4.0 **(leída)** | Atribución | — |
| Expresso, EARS | en | CC BY-NC 4.0 **(leída)** | No comercial | — |
| Emilia, Emilia-YODAS | multi | NC / CC BY; **conflicto** en el metadato **(leída)** | NC y audio de YouTube de terceros | — |
| Jenny (Dioco) | en (IE) | Propia, atribución obligatoria **(leída)** | No es CC0 | — |
| Elise | en | "mit", retirada por DMCA **(leída)** | Origen dudoso | — |
| Kyutai `expresso/`, `ears/` | en | CC BY-NC 4.0 **(leída)** | No comercial | Usar `voice-donations/` |
| Kyutai `vctk/`, `cml-tts/fr/`, `alba-mackenna/` | en, fr | CC BY 4.0 **(leída)** | Atribución | Ídem |
| Lingua Libre | multi | CC BY-SA 4.0 por defecto **(snippet)** | Share-alike; palabras sueltas | — |
| Spoken Wikipedia | multi | CC BY-SA **no verificado** | Share-alike | — |
| VOA, NASA, discursos presidenciales | es, en | Dominio público **(leída)** | **Riesgo de derecho a la voz**: personas identificables | — |
| YouTube, podcasts, locutores famosos | — | Copyright + derecho a la voz | Prohibido | — |
| Packs de "voice samples" en Discord o HF sin ficha | — | Sin licencia **(snippet)** | Procedencia desconocida | Kyutai o Voice-Zero |
| F5-TTS, F5-Spanish | es, en | CC BY-NC 4.0 **(leída)** / **(snippet)** | No comercial | — |
| Coqui XTTS-v2 | multi | CPML: restringe "the model **or its output**" **(leída)** | No comercial | — |
| Piper `lessac`, `ryan`, `hfc_female`, `amy`, `mls_10246` | en, es | Solo investigación, CC BY-NC-SA o no verificable **(leída)** | Ver [06](06-voces-sinteticas-y-diseno-de-voz.md) §2 | Piper `ald`, `davefx`, `cori`, `ljspeech`, `norman` |
| Microsoft, Google, ElevenLabs | multi | Términos de uso **(leída** / **snippet)** | Prohíben usar la salida para otro modelo o clonar sin consentimiento | — |

---

## 3. Si el Criterio Cambiara a CC BY

La mejor fuente latinoamericana sería **OpenSLR 71–75**, que tiene calidad de estudio, varios hablantes por país, transcripción en TSV y descargas de 0.6–0.9 GB por género. Exigiría atribución y share-alike, y no está resuelto si el share-alike alcanza al audio generado **(no verificado)**.
