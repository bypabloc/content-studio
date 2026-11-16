# Investigación: VoiceStudio y sus Motores para la Narración

> Investigación del 2026-11-15. Qué es [VoiceStudio](https://github.com/debpalash/VoiceStudio), cómo se usa cada una de sus herramientas, cómo rinden en español sus motores (OmniVoice, VoxCPM2, IndexTTS 2.5 y CosyVoice 3) medidos en la RTX 4060 de este repo, cómo escribir guiones con acentuación, entonación y emoción, qué audios grabar como referencia para clonar la voz, y una réplica del flujo de VoiceStudio verificada contra la app real. Es la base para sumar estos motores a `narration/tts.py`.

---

## Índice

| # | Capítulo | Contenido |
| :--- | :--- | :--- |
| 01 | [Método y fuentes](01-metodo-y-fuentes.md) | Acuerdos con el usuario, proceso, marcas de confianza, bloqueos |
| 02 | [VoiceStudio](02-voicestudio.md) | Qué es, qué motores envuelve, qué aporta su documentación, por qué motores directos |
| 03 | [OmniVoice](03-omnivoice.md) | Motor por defecto de VoiceStudio: instalación, controles, español medido, licencia no comercial |
| 04 | [VoxCPM2](04-voxcpm2.md) | 48 kHz, Apache-2.0, modos Hi-Fi y controlable, instrucciones en inglés vs español |
| 05 | [IndexTTS 2.5](05-indextts-2-5.md) | Vector de 8 emociones, `emo_text`, ritmo pausado, licencia bilibili |
| 06 | [CosyVoice 3](06-cosyvoice-3.md) | Etiquetas `[breath]`, `<strong>`, `instruct2`, la instalación más frágil |
| 07 | [Comparativa y licencias](07-comparativa-y-licencias.md) | Los seis motores lado a lado y recomendación por tipo de video |
| 08 | [Guion y pronunciación](08-guion-y-pronunciacion.md) | Acentuación, homógrafos, números, siglas, signos y marcas por motor |
| 09 | [Entonación y ritmo](09-entonacion-y-ritmo.md) | Altos y bajos del español, énfasis sin marcas, palabras por minuto por tipo de video |
| 10 | [Emociones y dirección](10-emociones-y-direccion.md) | Prompts por motor, sensaciones (sonrisa, susurro, respiración), recetas y antipatrones |
| 11 | [Audio de referencia](11-audio-de-referencia.md) | **Qué grabar para clonar la voz**: duración, técnica, contenido, kit de 11 clips y validación |
| 12 | [Recepción de la comunidad](12-recepcion-de-la-comunidad.md) | Qué gusta y qué se odia de cada motor |
| 13 | [Pruebas en GPU](13-pruebas-en-gpu.md) | Banco de pruebas, resultados por caso, etiquetas, emoción, velocidad, **audios para escuchar** |
| 14 | [Replicación de VoiceStudio](14-replicacion-de-voicestudio.md) | El flujo de `/generate` replicado y comparado contra la app real en Docker |
| 15 | [Aplicación a social-videos](15-aplicacion-social-videos.md) | Propuesta para `tts.py`: motores, parámetros, filtrado de marcas, piezas a reimplementar |
| — | [Herramientas de VoiceStudio](herramientas/README.md) | **16 herramientas, una por archivo**: clonación, diseño, audiolibros, lotes, doblaje, aislamiento, diarización, transcripción, dictado, API y CLI, MCP, integraciones, marca de agua, modelos y hardware, fine-tuning, instalación |

---

## Hallazgos Clave

1. **VoiceStudio no es un modelo**: es una app AGPL que orquesta más de 20 motores. Su motor por defecto, **OmniVoice, tiene pesos no comerciales** (CC-BY-NC); el autor lo confirmó a un youtuber monetizado, y la app exige aceptar esa licencia antes de generar ([02](02-voicestudio.md), [03](03-omnivoice.md), [14](14-replicacion-de-voicestudio.md)).
2. **Su flujo se replica con código propio** y se verificó contra la app real: duraciones, pausas, recorte, pico y loudness coinciden. La forma de onda no es idéntica por `torch.compile`, pero la misma semilla correlaciona 3–8× más que dos semillas distintas. Los defectos del modelo aparecen igual en la app ([14](14-replicacion-de-voicestudio.md)).
3. **Los cuatro motores corren en la 4060 de a uno**, con 2.2 a 5.8 GiB de VRAM. Las instalaciones están verificadas, con arreglos concretos para el segfault de `torch 2.15` y las trampas de CosyVoice ([07](07-comparativa-y-licencias.md), [13](13-pruebas-en-gpu.md)).
4. **Para uso comercial: VoxCPM2 (Apache-2.0) y CosyVoice 3 (Apache-2.0 con una duda)**. Los dos leyeron bien siglas y números en dígitos. CosyVoice es el único donde `[laughter]`, `[sigh]`, `[breath]` y `<strong>` funcionan sin leerse ([07](07-comparativa-y-licencias.md) §3).
5. **Cada motor falla distinto con el español**, medido:
   - OmniVoice **omite el tramo tras `…`**; `[pause]` y `<strong>` rompen la salida.
   - IndexTTS **lee "—" como "menos"**, lee mal los dígitos y lee todas las etiquetas.
   - VoxCPM2 **lee la instrucción en modo Hi-Fi**.
   - CosyVoice lee `[pause]` como "pausa".

   `tts.py` tiene que filtrar las marcas según el motor ([08](08-guion-y-pronunciacion.md) §5).
6. **Emoción sin regrabar** ([10](10-emociones-y-direccion.md)):
   - El vector de 8 emociones de IndexTTS produce cambios medibles y coherentes; la tristeza sale 1.5× más lenta.
   - Las instrucciones de VoxCPM2 y CosyVoice funcionan **en inglés**. En español cambian menos o se leen en voz alta.
7. **El ritmo lo pone la referencia.** OmniVoice, VoxCPM2 y CosyVoice copian los 198 ppm de la referencia de prueba; IndexTTS habla a ~130 ppm siempre. Para explicativos hay que grabar la referencia a 140–160 ppm ([09](09-entonacion-y-ritmo.md)).
8. **Audios para clonar la voz**:
   - Clips de **8–12 s** con la actitud desde el primer segundo (Chatterbox usa solo los primeros 6 s para el estilo).
   - Una emoción y un idioma por clip, en WAV de 48 kHz mono.
   - Sin denoise: baja la similitud de hablante (A).
   - Todo en una sola sesión, con la neutral al principio y al final.
   - Kit propuesto de 11 clips con textos y validación con ffmpeg ([11](11-audio-de-referencia.md)).
9. **Ningún motor abierto acepta IPA para español**: tildes, números en letras y respelling siguen siendo la herramienta. Las mayúsculas no dan énfasis en ninguno de los motores abiertos ([08](08-guion-y-pronunciacion.md)).
10. **Herramientas de VoiceStudio que vale la pena reimplementar** ([herramientas/](herramientas/README.md), [15](15-aplicacion-social-videos.md)):
    - semilla por bloque;
    - metadatos por toma;
    - masterización `broadcast`;
    - gramática longform (`[voice:]`, `[emotion:]`);
    - subtítulos por palabra;
    - marca de agua AudioSeal.

---

## Decisiones Tomadas

Respuestas del usuario del 2026-11-15:

| Tema | Decisión |
| :--- | :--- |
| Integración | **Motores directos** en `narration/tts.py`, cada uno en su venv (no la app ni su API) |
| Licencias | **Incluir los no comerciales** (OmniVoice, IndexTTS 2.5), marcados como tales |
| Motores | OmniVoice, VoxCPM2, IndexTTS 2.5, CosyVoice 3; solo español e inglés |
| Alcance de guion y emoción | Motores nuevos **más** Qwen3-TTS y Chatterbox |
| Pruebas | **Fuentes + pruebas en GPU** |
| Orden | **Investigar → preguntar → implementar** |
| Ubicación | `docs/research/voicestudio-narracion/` |
| Usos | Tutoriales, reels, storytelling, publicidad |
| Ampliaciones | Documentar cada herramienta de VoiceStudio; replicar VoiceStudio y probar la réplica |
| GPU | Detener el daemon Laya durante las pruebas y volver a detenerlo si reaparece |
| Licencia en la réplica | Aceptar la licencia de OmniVoice **solo** en el contenedor de prueba (borrado al terminar) |
| Costos | **Nada pago**: todo corre local y gratis |

---

## Preguntas Abiertas

| # | Pregunta | Por qué importa |
| :--- | :--- | :--- |
| 1 | ¿Qué motores implemento primero en `tts.py`? Propuesta: **VoxCPM2 y CosyVoice 3**, y OmniVoice e IndexTTS como opcionales no comerciales | Cada motor suma un venv y su filtrado de marcas |
| 2 | ¿Los videos se monetizan o son para clientes? | Define si OmniVoice e IndexTTS pueden usarse fuera de pruebas |
| 3 | ¿Grabas el kit de referencias (8–12 s) antes de implementar? | Todas las pruebas usan una referencia ajena; el acento y la similitud con tu voz no están medidos |
| 4 | ¿Masterización `broadcast` por defecto, opcional o con un objetivo de loudness para redes (−14 LUFS)? | Cambia el volumen de todas las salidas |
| 5 | ¿Implemento la emoción por párrafo (`[emocion: …]`) y la traducción de marcas por motor (`[risa]` → `[laughter]`)? | Es la pieza más útil y la más grande |
| 6 | ¿Actualizo en el mismo PR de implementación las guías existentes? Duraciones de [guiones/](../../../narration/docs/guiones/README.md) (11–17 s → 8–12 s), "Respiros y énfasis no se pueden pedir" en [formato-guion.md](../../../narration/docs/formato-guion.md) y `narration/voz/**/*.wav` en `.gitignore` | Hoy contradicen lo medido |
| 7 | ¿Qué conservo en disco? Imagen Docker de VoiceStudio (17.8 GB), repos de IndexTTS y CosyVoice en `tmp/` y venvs nuevos (~25 GB con pesos) | Espacio en disco |
