# Entonación (Altos y Bajos) y Ritmo

> Investigación del 2026-11-15. Cómo suben y bajan los tonos en español, cómo lograrlo sin marcas, qué ritmo usar por tipo de video y qué hacen los motores con el ritmo de la referencia, medido en la RTX 4060. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**, **medido** ([13](13-pruebas-en-gpu.md)); evidencia A/B/C.

---

## 1. Resumen

* **El ritmo lo pone la referencia.** La referencia de prueba va a 198 ppm y las salidas de OmniVoice y VoxCPM2 a 194 y 197 ppm (mediana) **medido**. Para narrar más lento hay que **grabar la referencia más lenta** o usar `speed` (OmniVoice, CosyVoice) o `duration_factor` (IndexTTS).
* **Los altos y bajos salen de la puntuación y de la sintaxis**, no de marcas: `¿…?` sube, `.` baja, las enumeraciones con "y" tienen una curva propia.
* **Ningún motor abierto controla el tono de una palabra.** El énfasis se logra moviendo la palabra al final del grupo entónico.

---

## 2. Tonemas del Español

La fonética describe cinco finales de grupo entónico (A, **(snippet)** de material de la UPV/EHU y la UCM):

| Tonema | Movimiento | Dónde aparece | Valor aproximado |
| :--- | :--- | :--- | :--- |
| Cadencia | Caída grande | Cierre de declarativa | ~ −8 st |
| Semicadencia | Caída menor | Miembros intermedios de una lista | −3 a −4 st |
| Suspensión | Nivel | Frase que queda abierta | < 1.5 st |
| Semianticadencia | Subida menor | Continuación | +2 a +3 st |
| Anticadencia | Subida grande | Pregunta absoluta (sí/no); penúltimo miembro de una lista con "y" | +4 a +5 st |

Valores en discurso parlamentario (A, **(snippet)** de la revista de fonética experimental de la UB). Se pueden medir con F0, como hace [13](13-pruebas-en-gpu.md).

### 2.1 Reglas Aplicables al Guion

| Situación | Lo que hace el español | Cómo escribirlo |
| :--- | :--- | :--- |
| **Enumeración con "y"** | El penúltimo sube, el último cae, el resto en semicadencia (Quilis 1993, A **(snippet)**) | "Tienes agenda, recetas, pagos y reportes." Cerrar con "y" da el "ya termino" |
| Enumeración sin "y" | Todos en semicadencia, el último en cadencia | Para listas abiertas o de ritmo |
| Enumeración con `…` | Queda en suspensión | Solo si se quiere dejar abierta |
| Pregunta absoluta | Anticadencia | `¿Ya revisaste la agenda?` |
| Pregunta pronominal (qué, cómo) | Suele terminar en cadencia (**no verificado**) | `¿Cómo lo haces?` no debería subir |
| Declarativa | Cadencia | Cerrar con `.`; la última palabra queda en la zona de menor energía, coherente con la regla local 22 (la última palabra del párrafo es frágil) |

**Medido** ([13](13-pruebas-en-gpu.md)):

| Motor | Final de `¿Ya revisaste la agenda de mañana?` | Enumeración: penúltimo → último |
| :--- | :--- | :--- |
| OmniVoice | +3.0 y +1.3 st (sube) | Sin dato fiable (pyin) |
| VoxCPM2 | −1.0 y +2.4 st (inconsistente) | "pagos" → "reportes": −8.8 st en una semilla (el último cae, como predice la fonética) |

La refinación para la notación de grabación de [guiones/](../../../narration/docs/guiones/README.md): marcar `↗` en el penúltimo miembro y `↘` en el último, no `→` en todos.

---

## 3. Énfasis sin Marcas

En español el foco neutro cae al **final del grupo entónico**. Técnicas (principio de foco final conocido en la fonética; como técnica de TTS **no verificado**):

| Técnica | Antes | Después |
| :--- | :--- | :--- |
| Mover al final del grupo | "Es gratis y es lo mejor." | "Y lo mejor de todo… es gratis para siempre." |
| Construcción escindida | "Esto cambia tu agenda." | "Lo que cambia tu agenda es esto." |
| Aislar con `…` antes | "Es muy importante." | "Es… importante." (no en OmniVoice: ver [08](08-guion-y-pronunciacion.md) §4) |
| Mayúsculas | "Es MUY importante." | **Sin efecto** en Qwen, OmniVoice y VoxCPM2 **medido** |

No dejar la palabra clave como **última del párrafo** (regla 22): ahí se pierde energía.

---

## 4. Ritmo por Tipo de Video

No hay estudios con método de palabras por minuto en español por género. Las cifras son de blogs y calculadoras (C, salvo donde se indica):

| Tipo | ppm sugeridas | Palabras por segundo | Comentario |
| :--- | :--- | :--- | :--- |
| Habla promedio en español | ~130 | 2.2 | Calculadora Omni **(snippet)** |
| Tutorial / demo | 140–160 | 2.3–2.7 | Speechify es-mx **(snippet)**; en inglés se sugiere ≤130: **conflicto** |
| Narración general | 130–160 | 2.2–2.7 | vivideo **(snippet)** |
| Publicidad | 150–180; spot de 30 s ≈ 75 palabras | 2.5–3.0 | **(snippet)** |
| Storytelling | Más lento y con más pausas largas | — | Sin cifra fiable en español |
| Reels / TikTok | Sin estándar | — | Emplifi (B): el ritmo pesa poco en la retención; el habla con sonido sube las vistas de 3 s un 8.8 % **(snippet)** |

**Lo medido en este repo va más rápido que esas cifras**: 198 ppm en la referencia de prueba y 194–197 ppm en las salidas. Se explica porque la referencia de prueba es rápida, no por el motor ([formato-guion.md](../../../narration/docs/formato-guion.md) mide 3.3 palabras/s de mediana con la misma referencia). Para videos explicativos conviene grabar las referencias propias a **140–160 ppm** (lo que ya pide [guiones/](../../../narration/docs/guiones/README.md)).

### 4.1 Gancho

* Gancho visual o hablado en el primer 1–1.5 s (C **(snippet)**): a 2.5–3.3 palabras por segundo, son **4–5 palabras** antes de la primera pausa.
* Las cifras de retención que circulan ("2.2× más vistas") no tienen estudio citable (C débil).

---

## 5. Control de Velocidad por Motor

| Motor | Parámetro | Medido |
| :--- | :--- | :--- |
| Qwen3 Base | No tiene; `tts.py` aplica `atempo` | — |
| Chatterbox | `exaggeration` alto acelera; `cfg_weight` ~0.3 compensa **(leída)** | — |
| OmniVoice | `speed`, `duration` | 0.9 → +11 %, 1.15 → −12 % de duración |
| VoxCPM2 | Solo instrucción ("slightly faster") | `cheerful and energetic` acortó 4.0 → 3.2 s en una semilla |
| IndexTTS 2.5 | `duration_factor` 0.5–2.0 | Ver [05](05-indextts-2-5.md) |
| CosyVoice 3 | `speed` | Ver [06](06-cosyvoice-3.md) |

`atempo` de ffmpeg (lo que usa hoy `tts.py`) cambia la velocidad sin cambiar el tono y funciona igual con cualquier motor.
