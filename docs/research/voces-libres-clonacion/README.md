# Investigación: Voces Libres para Clonar (CC0 y Dominio Público)

> Investigación del 2026-11-17. Cómo consigue y prepara la comunidad voces de calidad profesional para clonar con TTS abiertos, dónde hay voces gratuitas y libres para uso comercial (**solo CC0 o dominio público**) en español latino e inglés, qué derechos quedan aunque la licencia sea libre, y cómo clonan esas voces con **CosyVoice 3** medido en la RTX 4060 de este repo. Terminó en un catálogo de voces aprobadas en los 12 estilos, que se elige con `tts.py --voz`. Continúa a [voicestudio-narracion](../voicestudio-narracion/README.md), donde se estudió CosyVoice 3.

---

## Índice

| # | Capítulo | Contenido |
| :--- | :--- | :--- |
| 01 | [Método y fuentes](01-metodo-y-fuentes.md) | Acuerdos con el usuario, proceso, marcas de confianza, bloqueos |
| 02 | [Derechos: copyright y voz](02-derechos-copyright-y-voz.md) | **Por qué CC0 no alcanza**: las cuatro capas de derechos, leyes de EE. UU., la UE y Latinoamérica, plataformas, escalera de riesgo |
| 03 | [LibriVox en español](03-librivox-en-espanol.md) | La fuente grande de dominio público: lectores candidatos, API, receta, otras fuentes y descartes |
| 04 | [Inglés: LibriVox, Hi-Fi TTS y LJSpeech](04-ingles-librivox-ljspeech-y-otros.md) | Los 10 lectores que NVIDIA filtró, LJSpeech, Common Voice, VOA y descartes |
| 05 | [Donaciones CC0: Kyutai y Voice-Zero](05-donaciones-cc0-kyutai-y-voice-zero.md) | **Voces en español donadas con consentimiento para clonar**; Voice-Zero y su clip que era el aviso de LibriVox |
| 06 | [Voces sintéticas y diseño de voz](06-voces-sinteticas-y-diseno-de-voz.md) | Piper (`es_MX/ald` medido), voice design de VoxCPM2 y Qwen3, Kokoro, Parler; APIs descartadas por sus términos |
| 07 | [Descartados](07-descartados.md) | Todo lo que no es CC0 ni dominio público, con la licencia citada y un plan B |
| 08 | [Prácticas de la comunidad](08-practicas-de-la-comunidad.md) | De dónde sacan las referencias, duración, limpieza, cola que se filtra, trucos de CosyVoice 3, métricas y ExpPro, ética |
| 09 | [Preparar una referencia](09-preparar-una-referencia.md) | Lista de control y comandos para LibriVox y Kyutai; errores que aparecieron al automatizarlo |
| 10 | [Pruebas en GPU](10-pruebas-en-gpu.md) | **13 voces × 2 textos** con WER, SIM, UTMOS y ppm; experimentos de estilo (`instruct2`) y de inglés (`cross_lingual` frente a zero-shot); aprobación del catálogo; **audios para escuchar** |
| 11 | [Catálogo y aplicación](11-catalogo-y-aplicacion.md) | `voces/catalogo.json`, `voces.py`, `--voz` y el menú del CLI: criterios, estilos, voces y preguntas abiertas |

---

## Hallazgos Clave

1. **CC0 o dominio público liberan la grabación, no la voz.** El derecho a la propia voz (ELVIS Act, *Lehrman v. Lovo*, la LO 1/1982 española, el art. 53 del Código Civil argentino) sigue vigente aunque el audio sea libre. Lo que mide el riesgo es si una persona real es identificable ([02](02-derechos-copyright-y-voz.md)).
2. **La mejor fuente legal son las donaciones de Kyutai**: son CC0 y cada donante leyó una frase de consentimiento para la clonación. Hay unas 10 voces en español (Yesid, Andrea, John_Triguero, Richard_cuban, Enrique, una donante de Lima…), de calidad casera ([05](05-donaciones-cc0-kyutai-y-voice-zero.md)).
3. **LibriVox es la fuente grande, con calidad de audiolibro**: 565 libros en español, todos de dominio público en EE. UU. Pero **ningún lector dio consentimiento para clonar**, y el perfil no dice su país. En inglés, los 10 lectores de Hi-Fi TTS ya vienen filtrados por SNR y dieron consentimiento escrito a NVIDIA ([03](03-librivox-en-espanol.md), [04](04-ingles-librivox-ljspeech-y-otros.md)).
4. **Los datasets derivados licencian la compilación, no el audio**: MLS, CML-TTS, Hi-Fi TTS y LibriTTS son CC BY, pero el MP3 original del mismo lector en LibriVox es dominio público ([07](07-descartados.md)).
5. **En voces sintéticas con datos CC0 o de dominio público, en español latino solo está Piper `es_MX/ald`.** Clona sin errores, pero satura y es plana. La voz diseñada por texto (VoxCPM2) es la más limpia frente al derecho a la voz, aunque **no es CC0** ([06](06-voces-sinteticas-y-diseno-de-voz.md)).
6. **CosyVoice 3 clona bien todas las fuentes libres**: WER 0 en 23 de 26 clones. La calidad de la fuente pasa al clon: Karen Savage (LibriVox) lidera en español, con UTMOS 3.78, y Cori Samuel en inglés, con 4.47 ([10](10-pruebas-en-gpu.md) §3).
7. **La similitud WavLM-base-plus-sv tiene poco rango**: 0.95–0.99 la propia voz y hasta 0.95 una ajena. Detecta una voz que se pierde, pero no prueba identidad ([10](10-pruebas-en-gpu.md) §4).
8. **Para generar un estilo desde una base neutra, `instruct2` funciona y la instrucción en el prefijo no**: *triste* sale 1.3× más lenta, *dramática* 1.5× y *enérgica* más corta, fuerte y aguda. *Íntima* y *susurro* casi no cambian ([10](10-pruebas-en-gpu.md) §5).
9. **Para que una voz en español hable inglés, `cross_lingual` pierde la voz** (SIM 0.71–0.91; Andrea quedó más cerca de una voz inglesa que de sí misma), y el **zero-shot la conserva** (0.90–0.98) ([10](10-pruebas-en-gpu.md) §6).
10. **Catálogo: 5 de 8 voces aprobadas en los 12 estilos**. Aprobaron las 4 en español (Karen Savage, mpinedag, Yesid, Andrea) y Hannah. `instruct2` le quita la identidad a Cori Samuel (0.78–0.86), la mejor voz en zero-shot; John Van Stan y Nick quedaron a 0.01 del umbral en dos estilos alegres ([10](10-pruebas-en-gpu.md) §7).
11. **Normalizar la referencia no debe tocar las pausas internas**: el recorte de `grabar.py` las comprimía a 0.4 s y escondía pausas de 1.3–1.5 s en *dramática*. Ahora recorta solo los bordes ([10](10-pruebas-en-gpu.md) §7).
12. **No hace falta denoisear**: el clip procesado de Voice-Zero clonó igual que el crudo de LibriVox, y la comunidad midió que la limpieza baja la similitud (A) ([05](05-donaciones-cc0-kyutai-y-voice-zero.md) §3.1, [08](08-practicas-de-la-comunidad.md) §3.2).

---

## Decisiones Tomadas

Respuestas del usuario del 2026-11-17:

| Tema | Decisión |
| :--- | :--- |
| Fuentes | Datasets abiertos, voces sintéticas libres y prácticas de la comunidad (sin locutores pagos) |
| Licencia | **Solo CC0 o dominio público** |
| Idiomas | Español latino + inglés |
| Entregable | Carpeta nueva con esta estructura + pruebas en GPU |
| Ubicación (mensaje posterior) | `docs/research/`, con la estructura detallada de `voicestudio-narracion` |
| Aplicación (mensaje posterior) | Elegir la voz desde el CLI, entre las **aprobadas en todos los estilos** ([11](11-catalogo-y-aplicacion.md)) |
| Entrega (mensaje posterior) | Probar todo, commit, push y merge a `dev`, y volver a probar en `dev` |

Decisiones técnicas tomadas con los datos:

| Tema | Decisión | Base |
| :--- | :--- | :--- |
| Voces del catálogo | 4 en español (Karen Savage, mpinedag, Yesid, Andrea) y 4 en inglés (Cori Samuel, John Van Stan, Hannah, Nick) | Calidad medida + licencia + consentimiento ([11](11-catalogo-y-aplicacion.md) §5) |
| Estilos generados | `instruct2` con instrucción en inglés | [10](10-pruebas-en-gpu.md) §5 |
| `neutral-en` | Zero-shot, no `cross_lingual` | [10](10-pruebas-en-gpu.md) §6 |
| Umbrales | SIM ≥ 0.93, WER ≤ 0.15, 5–15 s, más los criterios de la guía de grabación | [11](11-catalogo-y-aplicacion.md) §3 |
| Audio en el repo | No: solo `catalogo.json`; el audio se reconstruye | El repo es público y el derecho a la voz no se cede con la licencia |

---

## Preguntas Abiertas

Para el usuario, al oído ([11](11-catalogo-y-aplicacion.md) §7):

1. ¿Qué voces en español suenan latino neutro?
2. ¿Alcanza la diferencia de *íntima* y *susurro* frente a *neutral*?
3. Para uso comercial con voces de LibriVox, ¿escribir a los lectores o limitarse a las de Kyutai?
