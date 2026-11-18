# Derechos: Copyright de la Grabación y Derecho a la Voz

> Investigación del 2026-11-17. Por qué "CC0" o "dominio público" no alcanza para clonar una voz, cuáles son las cuatro capas de derechos que hay que revisar, qué dicen las leyes y los casos vigentes en EE. UU., la UE y Latinoamérica, y qué exigen YouTube, TikTok y Meta. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**. **No es asesoría legal.**

---

## 1. Resumen

* **CC0 y el dominio público liberan el copyright de la *grabación*, no la *voz* de la persona.** La licencia CC0 lo dice explícitamente: "Affirmer disclaims responsibility for clearing rights of other persons" **(leída)**.
* **La voz está protegida por derechos de la personalidad**, independientes del copyright: el *right of publicity* en EE. UU., el derecho a la propia voz o imagen en España y Latinoamérica, y la voz como dato biométrico.
* **Lo que mide el riesgo es si una persona real es identificable** y si se usa con fines comerciales. En *Lehrman v. Lovo* (2025) se cayeron los reclamos de copyright sobre la voz clonada, pero sobrevivió el de derecho de publicidad **(snippet)**.
* **Por eso, en este proyecto, la fuente más limpia es una donación con consentimiento**, que da a la vez licencia CC0 y permiso explícito para clonar: las de Kyutai ([05](05-donaciones-cc0-kyutai-y-voice-zero.md)). Le siguen LibriVox (dominio público sin consentimiento para clonar) y las voces diseñadas por texto, que no son de nadie pero tampoco son CC0 ([06](06-voces-sinteticas-y-diseno-de-voz.md)).
* La regla 5 de `AGENTS.md` ("Clona solo voces con permiso de su dueño") **solo la cumplen las donaciones de Kyutai** y la voz propia.

---

## 2. Las Cuatro Capas de Derechos

| Capa | Qué cubre | ¿Afecta a la referencia? | Ejemplo |
| :--- | :--- | :--- | :--- |
| Código | El programa de inferencia | Casi nunca: MIT, Apache o GPL no alcanzan a la salida **(no verificado: lectura estándar)** | Piper (MIT; el fork activo es GPL-3.0) |
| Pesos | El modelo entrenado | Sí, si la licencia regula la salida | XTTS-v2 (CPML): "non-commercial use of a machine learning model **and its outputs**" **(leída)** |
| Datos de entrenamiento | Las grabaciones con que se entrenó | Indirectamente: datos NC o "solo investigación" contaminan los pesos | Piper `lessac` (Blizzard 2013): "exclusively for Research Purposes" **(leída)** |
| Voz y persona | El derecho de la persona sobre su voz | **Sí, y es independiente del copyright** | Lectores de LibriVox, Linda Johnson (LJSpeech) |

Una voz sirve para uso comercial solo si **las cuatro capas** lo permiten. Una referencia grabada (LibriVox, Kyutai) solo tiene la capa 4 y la de la grabación. Una referencia sintética (Piper, voice design) suma las capas 1 a 3 del modelo que la generó.

---

## 3. Qué Dice Cada Fuente sobre Clonación

| Fuente | Postura | Marca |
| :--- | :--- | :--- |
| **LibriVox** | "all our recordings are public domain (definitely in the USA, and maybe in your country as well)"; "anyone can use all our recordings however they wish (even to sell them)". **No menciona voz, TTS ni IA** | **(leída)** |
| LibriVox, foro | Los lectores preguntaron si donar al dominio público también renuncia a su imagen o semejanza, sin respuesta oficial. En r/librivox (feb. 2024), un lector dijo que la clonación es "one of the reasons I am doing less and less of it" | **(snippet)**. No hay demandas conocidas |
| **Kyutai voice-donations** | "Voices of volunteers submitted through our Unmute Voice Donation Project, licensed as CC0". El protocolo pide leer la frase "I consent to my voice being used for voice cloning", y se escucha en varios clips (Hannah, Enrique y la donante de Lima, en español) | **(leída)**, **medido** ([05](05-donaciones-cc0-kyutai-y-voice-zero.md)) |
| Hi-Fi TTS (NVIDIA) | "Although the source material … is in the public domain, … we sought the written consent of the speaker. We believe it is ethically responsible…" | **(leída)**, paper arXiv 2104.01497 |
| Common Voice | CC0 más una condición de descarga: "You agree to not attempt to determine the identity of speakers". Ante el pedido de prohibir el TTS, Mozilla respondió que "additional restrictions cannot be added to Creative Commons licenses" | **(snippet)** / **(leída)**, discourse.mozilla.org |
| VoxCPM (OpenBMB) | Los WAV de Voice Design "may [be] save[d], export[ed], publish[ed], redistribute[d], and use[d] commercially, subject to applicable law and third-party rights". Para clonar con referencia: "you must independently obtain lawful authorization for any reference audio" | **(leída)**, issues #407, #409 y #238 |
| NASA | Prohíbe mostrar "names, likenesses or other personality traits" de empleados actuales en material comercial | **(leída)** |

---

## 4. Leyes y Casos (Estado a Noviembre de 2026)

### 4.1 Estados Unidos

| Norma o caso | Qué dice | Estado | Marca |
| :--- | :--- | :--- | :--- |
| **ELVIS Act** (Tennessee) | Protege la voz "regardless of whether the sound contains the actual voice or a simulation of the voice" contra el uso comercial no autorizado | Vigente desde el 1/7/2024 | **(leída**, resumen de DWT; no el texto oficial**)** |
| **AB 1836** (California, Civil Code §3344.1) | Exige el consentimiento de los herederos para la réplica digital de un **intérprete fallecido** | Vigente desde el 1/1/2025 | **(snippet)**. La API de LibriVox muestra lectores fallecidos, como "Kara Shallenberg (1969-2023)": **evitarlos** |
| AB 2602 (California, Labor Code §927) | Anula las cláusulas de réplica digital sin una descripción "with reasonable specificity" | Vigente desde el 1/1/2025 | **(snippet)** |
| **NO FAKES Act** (S.4591 / H.R.8915) | Derecho federal sobre réplicas digitales, con notificación tipo DMCA | Reintroducida el 20/5/2026 y aprobada en la comisión judicial del Senado en junio de 2026. **No es ley** | **(leída**, Manatt**)**; fecha de la votación en **conflicto** (18, 22 o 26 de junio) |
| *Lehrman & Sage v. Lovo* (S.D.N.Y., 10/7/2025) | El copyright no protege "las cualidades abstractas de una voz"; **sobrevive** el reclamo de publicidad de Nueva York (Civil Rights Law §§ 50–51) | Fallo de primera instancia | **(snippet)** |
| US Copyright Office, *Part 2* (29/1/2025) | "Prompts alone, however, at this stage are unlikely to satisfy those requirements": la salida de IA sin control humano suficiente no tiene copyright | Informe oficial | **(leída)** |
| *Thaler v. Perlmutter* | Certiorari denegado el 2/3/2026: queda firme el requisito de autoría humana | Firme | **(snippet)** |

### 4.2 Unión Europea

| Norma | Qué dice | Estado | Marca |
| :--- | :--- | :--- | :--- |
| **AI Act, art. 50(4)** | Quien despliega un sistema que genera un *deepfake* de audio debe divulgar que es artificial; para obras evidentemente artísticas la divulgación es más ligera | Aplicable desde el **2/8/2026** | **(snippet)**; **conflicto** sobre las guías finales y un posible "AI Omnibus" |
| Dinamarca, proyecto L 49 | Daría derechos de autor sobre la propia cara y voz | Presentado el 8/10/2026, **no aprobado** | **(snippet)**, **conflicto** |

### 4.3 España y Latinoamérica

| País | Norma | Qué dice | Estado | Marca |
| :--- | :--- | :--- | :--- | :--- |
| España | LO 1/1982, art. 7.6 | Es intromisión ilegítima "la utilización del nombre, de la voz o de la imagen de una persona para fines publicitarios, comerciales o de naturaleza análoga" | Vigente | **(snippet)** del BOE |
| México | Reforma de la LFT y la LFDA (DOF, 14/5/2026) | Exige autorización escrita para clonar la voz con IA. Según Expansión, el art. 87 quedó limitado a "artistas intérpretes o ejecutantes": el ciudadano común no puede acudir al IMPI | Vigente | **(leída**, nota de prensa**)**; **conflicto** con notas que dicen que protege a todos |
| Colombia | Jurisprudencia (T-007/20); C-212/26 | El derecho a la imagen "también incluye la voz"; la C-212/26 avaló multas más altas por suplantación con IA | Jurisprudencia | **(snippet)** |
| Chile | Boletín 17.795-19 | Crea un "derecho a la integridad digital" que incluye la voz | Aprobado en general en la Cámara en julio de 2026: **proyecto** | **(snippet)** |
| Argentina | Código Civil y Comercial, art. 53 | Exige consentimiento para "captar o reproducir la imagen o la voz de una persona" | Vigente | **no verificado** |

---

## 5. Plataformas

| Plataforma | Regla | Marca |
| :--- | :--- | :--- |
| **YouTube** | Hay que divulgar el contenido realista que "makes a real person appear to say or do something they didn't do". Exento: "Cloning one's own voice to create voice overs or dubs". Clonar a **otra** persona real (un lector de LibriVox, un donante de Kyutai) no entra en la exención y conviene divulgarlo (deducción, **no verificado**) | **(leída)** support.google.com/youtube/answer/14328491 |
| TikTok | Exige etiquetar el contenido realista generado con IA, incluido el audio; detecta con C2PA | **(snippet)** |
| Meta | Etiqueta "AI info"; pide divulgar el audio "realistic-sounding" | **(snippet)** |

---

## 6. Escalera de Riesgo para este Proyecto

| Opción | Copyright de la referencia | Derecho a la voz | Consentimiento para clonar | Riesgo práctico |
| :--- | :--- | :--- | :--- | :--- |
| Voz propia grabada con `grabar.py` | Propio | Propio | Sí | Mínimo |
| **Donación Kyutai (CC0)** | Renunciado | Persona real, pero consintió | **Sí, explícito** | **Muy bajo** |
| Voz diseñada por texto (VoxCPM2, Qwen3 VoiceDesign) | Sin copyright (salida de IA) | Nadie identificable | No aplica | Muy bajo, pero **no es CC0** ([06](06-voces-sinteticas-y-diseno-de-voz.md)) |
| LibriVox (dominio público) | Inexistente en EE. UU. | Persona real | No | Bajo si no se usa su nombre ni es reconocible; mayor en España (art. 7.6) |
| Piper `es_MX/ald` (Unlicense) | Sin copyright | Persona real ("ald", sin identificar) | No | Bajo |
| Locutor famoso, YouTube, VOA, NASA | Con copyright o con nombre público | Persona identificable | No | **Alto: no usar** |

**Prácticas mínimas** que se repiten en todas las fuentes:

1. No usar el nombre del lector como gancho ni presentar la voz como si fuera esa persona.
2. No clonar a lectores fallecidos (AB 1836) ni a figuras públicas.
3. Etiquetar la narración como sintética en YouTube, TikTok y Meta, y en la UE desde agosto de 2026.
4. Guardar la procedencia de cada referencia: URL, licencia, fecha, tramo y transcripción. Es lo que hace [narration/voces/catalogo.json](../../../narration/voces/catalogo.json).
5. Si el uso es comercial y la voz es reconocible, **escribir al lector** y pedir permiso. Es gratis y elimina el riesgo.
