# Pruebas en GPU: 13 Voces Libres Clonadas con CosyVoice 3

> Investigación del 2026-11-17. El banco de pruebas en la RTX 4060 Laptop (8 GB): 13 referencias CC0 o de dominio público clonadas con CosyVoice 3 sobre los mismos textos, con WER, similitud de hablante, UTMOS, ritmo y loudness. Incluye dos experimentos que definieron `narration/voces.py`: cómo generar un estilo desde una base neutra y cómo hacer hablar inglés a una voz en español. Al final, los audios para escuchar. Índice en [README.md](README.md). Todo es **medido** salvo que se indique otra cosa.

---

## 1. Banco

| Pieza | Detalle |
| :--- | :--- |
| Scripts | `tmp/research-voces/` (gitignoreado): `elegir.py` (tramos), `clasificar.py` (donaciones de Kyutai), `banco.py` (generación), `analizar.py` (métricas), `modos.py` y `cruzado.py` (experimentos) |
| Motor | `Fun-CosyVoice3-0.5B-2512`, venv de `narration/motores/CosyVoice` (torch 2.11, Windows). La misma llamada de `tts.py`: `inference_zero_shot`, prefijo `You are a helpful assistant.<\|endofprompt\|>`, `text_frontend=False` |
| Semilla | 1234 para todo (`set_all_random_seed`) |
| Textos | Por idioma: **tutorial** ("En este video te muestro cómo configurar el proyecto en tres pasos…") e **historia** ("Aquella noche, el faro dejó de girar…"), con su versión en inglés |
| WER | whisper `large-v3-turbo`, texto sin tildes ni signos |
| SIM | Coseno de x-vectors de `microsoft/wavlm-base-plus-sv` entre la referencia y la salida. **SIM ajena** es el máximo contra las otras referencias del mismo idioma: sirve de calibración |
| Calidad | UTMOS (`tarepan/SpeechMOS` `utmos22_strong`). Entrenado con inglés: en español puntúa más bajo |
| Ritmo | Palabras por minuto sobre los tramos con voz (`librosa.effects.split`, 35 dB) |
| GPU | 3.45–3.5 GiB pico; 10–25 s por frase (RTF ~1.3–2) |

---

## 2. Referencias

| Referencia | Fuente | Licencia | Dur. | sr | LUFS | Pico real | Piso | ppm | UTMOS | F0 |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| es-karen | LibriVox, Karen Savage | PD | 11.7 | 44100 | −24.7 | −8.0 | −54.4 | 190 | 3.39 | 202 |
| es-mpinedag | LibriVox, mpinedag | PD | 11.0 | 44100 | −25.1 | −7.1 | −53.0 | 192 | 3.08 | 90 |
| es-epachuko | LibriVox, Epachuko | PD | 9.1 | 44100 | −27.0 | −7.9 | −70.2 | 165 | 2.74 | 91 |
| es-piper-ald | Piper `es_MX/ald` medium | Unlicense | 10.9 | 22050 | −15.2 | **+0.2** | −37.9 | 105 | 2.95 | 141 |
| es-kyutai-yesid | Kyutai, Yesid | CC0 | 10.0 | 24000 | −22.8 | −1.3 | −74.8 | 167 | 3.12 | 120 |
| es-kyutai-triguero | Kyutai, John_Triguero | CC0 | 10.0 | 24000 | −25.8 | −9.0 | −62.5 | 153 | 2.02 | 148 |
| es-kyutai-andrea | Kyutai, Andrea | CC0 | 10.0 | 24000 | −21.1 | −4.4 | −62.7 | 174 | 2.98 | 181 |
| en-vanstan | LibriVox, John Van Stan | PD | 11.8 | 44100 | −25.3 | −4.9 | −67.6 | 123 | 4.31 | 99 |
| en-cori | LibriVox, Cori Samuel | PD (CC0 en Archive.org) | 12.0 | 44100 | −22.7 | −6.5 | −67.5 | 205 | 4.42 | 223 |
| en-kasper | LibriVox, Maria Kasper | PD | 9.1 | 44100 | −24.3 | −8.9 | −73.4 | 187 | 3.83 | 231 |
| en-cori-vz | Voice-Zero, Cori Samuel (aviso de LibriVox) | CC0 | 8.9 | 44100 | −24.3 | −8.5 | −87.0 | 160 | 4.04 | 212 |
| en-kyutai-hannah | Kyutai, Hannah | CC0 | 10.0 | 24000 | −20.8 | −1.6 | −66.6 | **244** | 3.51 | 229 |
| en-kyutai-nick | Kyutai, Nick | CC0 | 10.0 | 24000 | −24.2 | −2.6 | −59.6 | 128 | 3.47 | 116 |

Las referencias del banco **no** se normalizaron: es el recorte crudo, para medir la fuente tal cual. El catálogo sí las normaliza ([11](11-catalogo-y-aplicacion.md)).

---

## 3. Clones

| Referencia / texto | Dur. (s) | Gen. (s) | WER | SIM | SIM ajena | UTMOS | ppm |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| es-mpinedag / tutorial | 12.6 | 14.3 | 0 | 0.985 | 0.892 | 3.49 | 157 |
| es-mpinedag / historia | 9.2 | 11.4 | 0 | 0.985 | 0.897 | 3.13 | 182 |
| **es-karen / tutorial** | 12.3 | 19.2 | 0 | **0.993** | 0.828 | **3.78** | 161 |
| **es-karen / historia** | 9.4 | 13.4 | 0 | 0.962 | 0.905 | **3.66** | 189 |
| es-epachuko / tutorial | 14.6 | 16.1 | 0 | 0.991 | 0.905 | 3.11 | 148 |
| es-epachuko / historia | 9.8 | 14.7 | 0 | 0.982 | 0.883 | 2.60 | 192 |
| es-piper-ald / tutorial | 12.5 | 20.9 | 0 | 0.989 | 0.867 | 3.49 | 141 |
| es-piper-ald / historia | 8.4 | 10.9 | 0 | 0.975 | 0.827 | 2.91 | 173 |
| es-kyutai-yesid / tutorial | 15.5 | 19.9 | 0.034 | 0.963 | 0.951 | 3.45 | 129 |
| es-kyutai-yesid / historia | 9.8 | 14.3 | 0 | 0.976 | 0.947 | 3.23 | 179 |
| es-kyutai-triguero / tutorial | 13.2 | 15.2 | **0.103** | 0.990 | 0.919 | 2.33 | 155 |
| es-kyutai-triguero / historia | 8.4 | 9.6 | 0 | 0.979 | 0.912 | 2.46 | 197 |
| es-kyutai-andrea / tutorial | 15.0 | 15.9 | 0.034 | 0.970 | 0.865 | 3.17 | 138 |
| es-kyutai-andrea / historia | 9.7 | 11.0 | 0 | 0.978 | 0.844 | 3.38 | 163 |
| en-vanstan / tutorial | 16.1 | 24.7 | 0 | 0.955 | 0.808 | 3.98 | 166 |
| en-vanstan / historia | 7.6 | 9.7 | 0 | 0.949 | 0.840 | 4.49 | 186 |
| **en-cori / tutorial** | 11.7 | 16.0 | 0 | 0.987 | 0.973* | **4.47** | 202 |
| **en-cori / historia** | 9.5 | 22.7 | 0 | 0.981 | 0.950* | **4.47** | 176 |
| en-kasper / tutorial | 11.8 | 21.8 | 0 | 0.971 | 0.749 | 3.67 | 192 |
| en-kasper / historia | 10.3 | 21.7 | 0 | 0.983 | 0.750 | 4.10 | 170 |
| en-cori-vz / tutorial | 11.4 | 19.9 | 0 | 0.988 | 0.973* | 4.38 | 208 |
| en-cori-vz / historia | 10.0 | 15.6 | 0 | 0.984 | 0.966* | 4.46 | 170 |
| en-kyutai-hannah / tutorial | 9.5 | 15.0 | 0 | 0.965 | 0.782 | 3.89 | **241** |
| en-kyutai-hannah / historia | 8.6 | 10.8 | 0 | 0.957 | 0.792 | 3.89 | 188 |
| en-kyutai-nick / tutorial | 13.0 | 15.7 | 0 | 0.977 | 0.863 | 3.59 | 162 |
| en-kyutai-nick / historia | 11.0 | 14.1 | 0 | 0.972 | 0.841 | 3.70 | 133 |

\* `en-cori` y `en-cori-vz` son la misma persona: su SIM ajena es en realidad SIM propia entre dos grabaciones distintas.

Los únicos errores de WER son imperativos cambiados en el tutorial ("instalas" → "instala", "ajustas" → "ajusta"), todos en donaciones de Kyutai en español.

---

## 4. Lectura

1. **CosyVoice 3 clona bien todas las fuentes libres**: WER 0 en 23 de 26 clones y ≤ 0.10 en el resto.
2. **La similitud WavLM-base-plus-sv tiene poco rango**: la propia voz da 0.95–0.99 y la ajena más parecida, 0.75–0.95. Yesid queda a 0.963 de su referencia y a 0.951 de otra voz. **La SIM detecta una voz que se pierde (cae por debajo de 0.9), pero no prueba la identidad**: para eso hace falta el oído o un segundo verificador (ERes2Net, [08](08-practicas-de-la-comunidad.md) §5).
3. **La calidad de la fuente se nota en el clon**: en español, Karen (UTMOS 3.78/3.66) supera a las donaciones caseras (2.33–3.45). En inglés, LibriVox (Cori 4.47) supera a Kyutai (3.59–3.89). John_Triguero, con la peor referencia (UTMOS 2.02), dio los peores clones.
4. **El ritmo de la referencia pasa al clon** en las voces rápidas: Hannah habla a 244 ppm y su tutorial salió a 241. En las lentas no tanto: Van Stan, a 123 ppm, salió a 166 y 186. Para explicativos hay que elegir referencias de 140–180 ppm ([voicestudio-narracion/09](../voicestudio-narracion/09-entonacion-y-ritmo.md)).
5. **El procesado de Voice-Zero no cambió las métricas** frente al crudo de LibriVox (UTMOS 4.38–4.46 contra 4.47; SIM 0.984–0.988 contra 0.981–0.987).
6. **Piper `ald` clona sin errores**, pero su referencia satura y tiene prosodia plana (105 ppm).

---

## 5. Experimento: Cómo Generar un Estilo desde una Base Neutra

Base: `es-karen`. Textos del kit de grabación (`narration/voz/<estilo>.txt`). Tres modos:

* **control**: zero-shot sin instrucción.
* **instruct2**: `inference_instruct2` con la instrucción en inglés.
* **prefijo**: zero-shot con la instrucción dentro del prefijo (#1895).

| Estilo | Modo | SIM | Duración (s) | F0 (Hz) | Rango F0 (st) | RMS (dB) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| neutral | control | 0.990 | 10.24 | 203 | 8.0 | −21.4 |
| energica | control | 0.992 | 8.88 | 208 | 5.6 | −22.9 |
| energica | **instruct2** | 0.973 | **7.80** | **217** | **7.7** | **−18.5** |
| energica | prefijo | 0.979 | 8.40 | 210 | 5.9 | −23.1 |
| triste | control | 0.988 | 7.88 | 210 | 5.5 | −23.4 |
| triste | **instruct2** | 0.964 | **10.44** | 208 | 5.5 | −20.2 |
| triste | prefijo | 0.988 | 7.40 | 205 | 6.6 | −23.7 |
| dramatica | control | 0.988 | 8.64 | 202 | 6.0 | −22.8 |
| dramatica | **instruct2** | 0.977 | **13.12** | 197 | 4.4 | −22.4 |
| dramatica | prefijo | 0.982 | 8.92 | 196 | 5.9 | −24.6 |
| intima | control | 0.989 | 6.36 | 203 | 4.6 | −22.7 |
| intima | instruct2 | 0.992 | 6.84 | 203 | 4.9 | −23.7 |
| intima | prefijo | 0.985 | 6.40 | 199 | 6.8 | −23.7 |
| susurro | control | 0.989 | 6.36 | 203 | 4.6 | −22.7 |
| susurro | instruct2 | 0.974 | 5.28 | 201 | 7.9 | −20.0 |
| susurro | prefijo | 0.980 | 7.32 | 196 | 22.7 | −23.2 |

**Conclusión**:

* **La instrucción en el prefijo casi no cambia nada**: manda la entrega de la referencia.
* **`instruct2` produce cambios medibles y coherentes con la emoción**, pagando 0.01–0.03 de SIM:
  * *triste*: 1.3× más lenta;
  * *dramática*: 1.5× más lenta, con pausas;
  * *enérgica*: más corta, 4 dB más fuerte, F0 +9 Hz y más rango.
* *Íntima* y *susurro* casi no cambian. Coincide con lo medido antes: "los estilos no se siguen, las emociones sí" ([voicestudio-narracion/10](../voicestudio-narracion/10-emociones-y-direccion.md) §2.3).

`voces.py` usa `instruct2` para los estilos con instrucción.

---

## 6. Experimento: `neutral-en` de una Voz en Español

`neutral-en` es la referencia en inglés que usa `tts.py --idioma en`. Para una voz en español hay que generarla. Se compararon dos modos con dos semillas cada uno. "Otra es" es la SIM con otra voz en español; "EN máx.", con la voz inglesa más parecida del banco.

| Voz | Modo | SIM base (2 semillas) | Otra ES máx. | EN máx. |
| :--- | :--- | :--- | ---: | ---: |
| karen | `cross_lingual` | 0.824 / 0.909 | 0.79 | 0.86 |
| karen | zero-shot | **0.931 / 0.960** | 0.90 | 0.83 |
| mpinedag | `cross_lingual` | 0.803 / 0.842 | 0.63 | 0.81 |
| mpinedag | zero-shot | **0.978 / 0.969** | 0.82 | 0.79 |
| yesid | `cross_lingual` | 0.710 / 0.835 | 0.75 | 0.85 |
| yesid | zero-shot | **0.967 / 0.897** | 0.87 | 0.87 |
| andrea | `cross_lingual` | 0.796 / 0.804 | 0.72 | **0.944** |
| andrea | zero-shot | **0.975 / 0.970** | 0.82 | 0.79 |

**`cross_lingual` pierde la voz.** En Andrea, el clon queda más cerca de una voz inglesa (0.944) que de su propia base (0.796). El zero-shot, con la transcripción en español y el texto en inglés, conserva la identidad (0.90–0.98). Es probable que arrastre acento español (**no verificado** al oído), lo mismo que reportan OmniVoice, Chatterbox y VoxCPM2 ([voicestudio-narracion/11](../voicestudio-narracion/11-audio-de-referencia.md) §4). `voces.py` usa zero-shot.

---

## 7. Aprobación del Catálogo

Resultado de `python narration/voces.py --construir …` con los criterios de [11](11-catalogo-y-aplicacion.md) §3. Detalle por estilo en `narration/voces/<voz>/aprobacion.json`.

Corrida final (`--construir todas --forzar`, con el recorte de bordes corregido; ver abajo):

| Voz | Idioma | Resultado | SIM mín. | WER máx. | Rondas | Estilos que no aprobaron (SIM de la mejor semilla) |
| :--- | :--- | :--- | ---: | ---: | ---: | :--- |
| **karen-savage** | es | **Aprobada 12/12** | 0.950 | 0.08 | 2 | — |
| **mpinedag** | es | **Aprobada 12/12** | 0.950 | 0.11 | 2 | — |
| **yesid** | es | **Aprobada 12/12** | 0.931 | 0.08 | 2 | — |
| **andrea** | es | **Aprobada 12/12** | 0.947 | 0.08 | 2 | — |
| **hannah** | en | **Aprobada 12/12** | 0.938 | 0.12 | 2 | — |
| cori-samuel | en | Reprobada 3/12 | 0.781 | 0.05 | 3 | amistosa 0.80, suave 0.78, experta 0.84, clara 0.80, estable 0.83, energica 0.84, dramatica 0.79, triste 0.86, susurro 0.83 |
| john-van-stan | en | Reprobada 10/12 | 0.924 | 0 | 3 | amistosa 0.93, experta 0.92 |
| nick | en | Reprobada 10/12 | 0.919 | 0.04 | 3 | amistosa 0.92, energica 0.92 |

Lectura:

1. **Todas las voces en español aprobaron**, incluidas las donaciones caseras de Kyutai. De las inglesas, solo aprobó Hannah.
2. **`instruct2` pierde la voz de Cori Samuel**: 0.78–0.86 en 9 estilos y con 3 semillas, cuando en zero-shot había sido la mejor del banco (0.981–0.987, §3). El modo instrucción reemplaza la entrega de la referencia ([voicestudio-narracion/10](../voicestudio-narracion/10-emociones-y-direccion.md) §2.3) y, con esta voz, también parte del timbre. John Van Stan y Nick quedaron a 0.01 del umbral en dos estilos alegres: *amistosa* y *experta*, y *amistosa* y *enérgica*.
3. **La primera corrida** (con el recorte viejo, que comprimía las pausas internas a 0.4 s) dio exactamente las mismas 5 aprobadas. **La corrida final rechazó 6 clips de *dramática*** con pausas internas de 1.3–1.5 s, que antes quedaban escondidas. Los reintentos dieron versiones sin pausas largas. El arreglo de `referencia.procesar()` (recortar solo los bordes) cambia el ritmo de toda referencia normalizada, incluidas las grabaciones propias de `grabar.py`.
4. Ninguna voz necesitó más de 2 rondas para aprobar. Las reprobadas agotaron las 3.

---

## 8. Audios para Escuchar

En `out/narration/research-voces/` (gitignoreado):

* `<referencia>__tutorial.wav` y `<referencia>__historia.wav`: los 26 clones del banco (§3).
* `modos/<estilo>__{control,instruct2,prefijo}.wav`: el experimento de §5.
* `cruzado/<voz>__{cross,zero}__<semilla>.wav`: el experimento de §6.

Y el catálogo construido, en `narration/voces/<voz>/<estilo>.wav`.

**Lo que hay que decidir al oído**, porque ninguna métrica lo mide:

1. El acento de cada voz en español: ¿suena latino neutro?
2. Si *triste*, *dramática* y *enérgica* suenan a lo que dicen, y si *íntima* y *susurro* se distinguen de *neutral*.
3. Si `neutral-en` de las voces en español tiene un acento aceptable para narrar en inglés.
