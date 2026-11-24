# Audios de Referencia: Qué Grabar para Clonar la Voz

> Investigación del 2026-11-15. Qué audios tener como base para clonar la voz con los seis motores (Qwen3-TTS Base, Chatterbox, OmniVoice, VoxCPM2, IndexTTS 2.5, CosyVoice 3): duración, condiciones técnicas, contenido, emoción, kit propuesto y cómo validarlo. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](01-metodo-y-fuentes.md) §3).

---

## 1. Resumen

* **8–12 s de habla continua por clip** es el rango que sirve a los seis motores. La actitud tiene que estar **desde el segundo 0**: Chatterbox toma el estilo de los primeros 6 s.
* **Una emoción por clip, un idioma por clip.** El clon copia la entrega (ritmo, energía, emoción, acento y sala), no solo el timbre. Todos los proveedores y motores lo confirman (B).
* **Una sola sesión** para toda la biblioteca: mismo micrófono, distancia y ganancia. Grabar la neutral al principio y repetirla al final como control.
* **Grabar en WAV**, mono, 48 kHz, sin compresor, sin EQ y **sin denoise**. Limpiar la referencia baja la similitud de hablante (A).
* **Cada `.wav` con su `.txt` exacto.** Qwen, CosyVoice (zero-shot) y VoxCPM2 (modo Hi-Fi) lo usan.
* Para IndexTTS 2.5 conviene además una **referencia neutral de timbre** y, opcionalmente, clips de emoción aparte.

---

## 2. Duración, Recorte y Transcripción por Motor

| Motor | Óptima | Qué hace con un clip largo | Transcripción | Varias referencias | Fuente |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen3-TTS Base** | 10–15 s (comunidad); Alibaba 10–20 s, máx. 60 | Usa todo | **Sí** (modo ICL). Si no coincide, clona peor y puede trabar la primera palabra | No | README Qwen **(leída)**; Alibaba **(leída)**; ocdevel **(leída, C/B)** |
| **Chatterbox Multilingual** | ~10 s | **Estilo: primeros 6 s. Timbre del decodificador: primeros 10 s.** El resto solo entra al embedding | No | No | `mtl_tts.py`: `ENC_COND_LEN = 6 * S3_SR`, `DEC_COND_LEN = 10 * S3GEN_SR` **(leída)** |
| **OmniVoice** | **3–10 s** | Sin corte duro; más largo "may degrade cloning quality". VoiceStudio usa máx. 20 s | Opcional; sin ella carga Whisper (más VRAM; OOM en 8 GB, issue #282) | No (se cachea el prompt) | README OmniVoice **(leída)**; VoiceStudio **(leída)** |
| **VoxCPM2** | ≥5 s; 5–30 s práctico | VoiceStudio corta a 30 s | Solo en modo Hi-Fi (`prompt_wav_path` + `prompt_text`, exacta) | Dos rutas: timbre (`reference_wav_path`) y continuación (`prompt_wav_path`) | README y cookbook **(leída)** |
| **IndexTTS 2.5** | 8–15 s | **Corta a 15 s** (también el clip de emoción) | No | **Sí**: timbre + clip de emoción | `infer_v2_5.py` L627, L682 **(leída)** |
| **CosyVoice 3** | ~3–30 s | **Rechaza > 30 s** (assert) | Sí en zero-shot (con `<\|endofprompt\|>`); no en cross-lingual | No | `frontend.py` L97 **(leída)** |

**Contradicción con la guía actual** ([narration/docs/guiones/README.md](../../../narration/docs/guiones/README.md)): pide 11–17 s por estilo. Con Chatterbox lo que pasa después del segundo 10 no llega al decodificador, y OmniVoice recomienda ≤10 s. Propuesta: **bajar a 8–12 s** y mover lo más representativo del estilo al inicio.

---

## 3. Condiciones Técnicas

| Aspecto | Recomendación | Base |
| :--- | :--- | :--- |
| Formato | WAV PCM 24 bits (maestro) o 16 bits, **mono, 48 kHz**. Los modelos remuestrean a 16/22.05/24 kHz | Motores **(leída)**; Alibaba ≥24 kHz **(leída)** |
| MP3, m4a, audio de WhatsApp | Evitar como fuente: el corte de banda y los artefactos se clonan. Convertir a WAV no recupera la calidad | **no verificado** con estudio; ElevenLabs acepta MP3 ≥192 kbps porque hace fine-tuning **(leída)** |
| Nivel | RMS −23 a −18 dBFS; **true peak ≤ −3 dBTP** | ElevenLabs IVC/PVC **(leída)**, igual que ACX **(snippet)** |
| Piso de ruido | ≤ −60 dBFS en los silencios (SNR ≥ 40 dB). Un piso de −inf indica gate o silencio digital | ACX **(snippet)** |
| Sala | Lo más seca posible: "a clip recorded in an echoey room clones echoey". Cuarto chico con ropa o cortinas, o un clóset; frazada detrás del micrófono; apagar ventilador y aire | VoiceStudio **(leída)**; ElevenLabs **(leída)**; Alibaba ≤10 m² **(leída)** |
| Distancia | 10–20 cm, **constante** en todas las tomas, un poco de costado; filtro antipop | Alibaba 10 cm, ElevenLabs "dos puños", Fish "una mano" **(leída)**: **conflicto** menor, todos en el rango |
| Micrófono | En sala sin tratar, un dinámico cardioide rechaza más la habitación; un condensador USB solo con sala tratada; un celular sirve en sala seca | Fish **(leída)**; ElevenLabs PVC **(leída)**; lo del dinámico es práctica de audio, **no verificado** |
| Silencios | 0.3–0.5 s al inicio y al final; pausas internas ≤0.7 s (nunca >2 s) | Alibaba **(leída)**; Cartesia: las pausas largas hacen derivar la voz **(snippet)** |
| Procesado | Solo ganancia lineal a ~−18 LUFS / −3 dBTP. **Sin compresor, limitador agresivo ni EQ** | **no verificado** (ningún motor documenta normalización) |
| **Denoise** | **Evitarlo.** Si hay ruido, regrabar | arXiv 2602.05770: el denoise baja la similitud de hablante (SECS 0.35 → 0.28 en F5-TTS) **(leída, A)**; Cartesia "any postprocessing will reduce the similarity" **(snippet)**. ElevenLabs sugiere "a noise remover if needed" **(leída)**: **conflicto** suave |

**Medido en esta sesión:** la referencia de prueba `narration/voz/prueba/experta.wav` tiene true peak **−0.2 dBFS**, −17 LUFS y piso **−inf** (silencio digital). No cumple los umbrales: sirve para pruebas, no como modelo de grabación.

---

## 4. Contenido: Qué Decir

* **Hablar como se quiere que hable el clon**, no como locutor leyendo: "Speak the way you want the clone to speak" (Cartesia **(leída)**); una lectura plana da un clon plano (ElevenLabs **(leída)**).
* **Frases completas** a ritmo constante, sin acelerar al inicio ni al final; acelerar provoca tartamudeo en la síntesis (Alibaba **(leída)**).
* **Entonación natural dentro de un solo estilo**: el audio "very dynamic" da resultados menos predecibles (ElevenLabs **(leída)**).
* **Sin muletillas ni respiraciones fuertes**: se reproducen (ElevenLabs **(leída)**). Si se quieren respiraciones en la salida de OmniVoice, sí hay que grabarlas (VoiceStudio **(leída)**).
* **Un idioma por referencia.** Con una referencia en español, el inglés sale con acento español y viceversa (OmniVoice, Chatterbox, VoxCPM2 #321 **(leída)**). Para videos en inglés, grabar una referencia en inglés.

### 4.1 Rasgos del Español Latino Neutro que Conviene Cubrir

Un clip de 10 s no alcanza para un corpus balanceado: el balance importa en la **biblioteca completa**. Cada clip debería incluir los rasgos que delatan el acento (conocimiento lingüístico general, **no verificado** con fuente en esta sesión):

| Rasgo | Ejemplos |
| :--- | :--- |
| Seseo (c, z, s = [s]) | decisión, sencillo, empezar |
| Yeísmo sin "sh" | llamar, ya, proyecto |
| Vibrante simple y múltiple | pero/perro, caro/carro, arranca |
| /x/ suave | jugar, gente, trabajo |
| "d" intervocálica completa | todo, nada, terminado |
| /s/ final completa | estos, mismos, después |
| ñ y ch | año, señal, mucho, noche |
| Agudas, llanas, esdrújulas | canción, fácil, rápido, práctica |

Corpus de texto disponibles: **Sharvard** (700 frases balanceadas, grabado por hablantes peninsulares, sirve como texto leído con seseo) **(snippet)**; **DIMEx100** (español mexicano, 5 010 frases; uso comercial requiere convenio con la UNAM) **(snippet)**.

---

## 5. Emoción en la Referencia

| Motor | Cómo se cambia la emoción | Consecuencia para la biblioteca |
| :--- | :--- | :--- |
| Qwen3-TTS Base | Solo con la referencia | **Una referencia por estilo** es la única palanca |
| OmniVoice | Solo con la referencia (el único estilo de `instruct` es `whisper`, y solo en diseño) | Igual |
| Chatterbox | Referencia + `exaggeration` / `cfg_weight` | Una referencia por estilo; ajustar con los parámetros |
| VoxCPM2 | Referencia **o** instrucción `(…)` con `reference_wav_path` | Una neutral + instrucciones, o una por estilo en modo Hi-Fi |
| CosyVoice 3 | Referencia (zero-shot) **o** instrucción (`instruct2`, que **ignora** la entrega de la referencia) | Igual que VoxCPM2 |
| **IndexTTS 2.5** | **Timbre y emoción separados**: referencia neutral + vector, texto o clip de emoción (`emo_alpha`) | **Una neutral basta**; los clips de emoción pueden ser de 5–8 s |

Fuentes: [03](03-omnivoice.md) a [06](06-cosyvoice-3.md), Chatterbox README **(leída)**. Consenso de proveedores (B): **una referencia por estilo, sin mezclar estilos en un clip** (ElevenLabs PVC, Fish, Cartesia **(leída)**).

* **No sobreactuar**: una referencia exagerada se vuelve el piso de toda la narración (local + ElevenLabs).
* **Sonrisa audible**: los oyentes detectan el habla sonriente, incluso susurrada (Tartter 1980; Quené **(snippet, A)**). Grabar `amistosa` sonriendo de verdad.
* **Susurro**: casi sin voz sonora, el timbre se pierde. Grabar además una voz `intima` (baja y cercana), que conserva el timbre (**no verificado**).

### 5.1 Cómo Grabar la Biblioteca para que Suene Consistente

1. **Una sola sesión**, misma posición (marcar con cinta), misma ganancia. No ajustar la ganancia entre estilos: la diferencia de intensidad es parte de la emoción; se normaliza después con ganancia lineal.
2. Empezar por la **neutral** (ancla de timbre) y repetirla al final para comprobar que la voz no cambió por cansancio.
3. Calentar 5 min; agua sin gas; evitar lácteos y café justo antes (sonido de boca) (C).
4. Tres tomas por estilo y elegir la más natural (ya está en la guía actual).

---

## 6. Kit de Referencias Propuesto

**8–12 s por clip**, actitud desde el primer segundo, una emoción por clip, todo en la misma sesión. Maestro WAV 48 kHz 24 bits mono; copia de trabajo a −18 LUFS / −3 dBTP. Cada `.wav` con su `.txt`.

**Los textos exactos, la actitud, la versión marcada y el orden de grabación de cada clip están en [narration/docs/guiones/](../../../narration/docs/guiones/README.md)** (decisión del usuario del 2026-11-15). Resumen:

| # | Archivo | Duración | Uso |
| :--- | :--- | :--- | :--- |
| 0 | `neutral.wav` | 10–12 s | Ancla de timbre; IndexTTS y VoxCPM2 con emoción por parámetro; comparación entre motores |
| 1 | `amistosa.wav` | 9–11 s | Reels, saludos, llamadas a la acción, grabado sonriendo |
| 2 | `experta.wav` | 10–12 s | Demos y tutoriales |
| 3 | `clara.wav`, `estable.wav`, `suave.wav` | 10–12 s c/u | Tutoriales paso a paso, corporativo, temas sensibles |
| 4 | `energica.wav` | 8–10 s | Publicidad, gancho de reel |
| 5 | `dramatica.wav` | 10–12 s | Storytelling, tráiler |
| 6 | `triste.wav` | 10–12 s | Historias emotivas |
| 7 | `intima.wav` | 9–11 s | Voz baja y cercana: secretos, cierres |
| 8 | `susurro.wav` (opcional) | 7–9 s | Solo efectos; probar antes de usar |
| 9 | `neutral-en.wav` | 10–12 s | Videos en inglés (evita el acento cruzado) |
| 10 | `neutral-fin.wav` | 10–12 s | Control: mismo texto que 0, al final de la sesión |

Opcional para IndexTTS 2.5: 6 clips de emoción de 5–8 s (alegría, tristeza, enojo, miedo, sorpresa, calma) para usar como `emo_audio_prompt` sobre `neutral.wav` ([guion 11](../../../narration/docs/guiones/11-emociones.md)).

**Qué referencia usa cada motor:**

| Motor | Referencia |
| :--- | :--- |
| Qwen3 Base, OmniVoice, CosyVoice 3 (zero-shot) | La del estilo + su `.txt` |
| Chatterbox | La del estilo; `exaggeration` 0.6–0.8 en `energica` y `dramatica` |
| VoxCPM2 | La del estilo en modo Hi-Fi (máxima similitud), o `neutral.wav` + instrucción |
| IndexTTS 2.5 | `neutral.wav` + vector o clip de emoción, o la del estilo sola |

---

## 7. Validación con ffmpeg

```bash
f=narration/voz/energica.wav
# Formato: mono, >= 44.1 kHz, PCM
ffprobe -v error -show_entries stream=codec_name,sample_rate,channels,bits_per_sample:format=duration -of default=nw=1 "$f"
# Nivel, pico, clipping, piso de ruido
ffmpeg -hide_banner -nostats -i "$f" -af "astats=measure_perchannel=none:measure_overall=Peak_level+RMS_level+RMS_trough+Noise_floor+Flat_factor" -f null - 2>&1 | grep -i "peak\|rms\|noise\|flat"
# Loudness y true peak
ffmpeg -hide_banner -nostats -i "$f" -af ebur128=peak=true -f null - 2>&1 | tail -n 12
# Silencios en los bordes y pausas internas
ffmpeg -hide_banner -nostats -i "$f" -af silencedetect=n=-45dB:d=0.25 -f null - 2>&1 | grep silence_
# Espectrograma (techo de MP3, zumbido de 50/60 Hz, música, reverberación)
ffmpeg -y -i "$f" -lavfi showspectrumpic=s=1200x500:legend=1 out/ref-espectro.png
# Normalizar con ganancia lineal, una pasada
ffmpeg -i bruto.wav -af loudnorm=I=-18:TP=-3:LRA=11:linear=true -ac 1 -ar 48000 -c:a pcm_s16le "$f"
```

| Check | Aprobado |
| :--- | :--- |
| Duración | 8–12 s (máx. 15 s por IndexTTS) |
| Formato | 1 canal, ≥44.1 kHz, PCM |
| RMS global / loudness | −23 a −16 dBFS / −20 a −16 LUFS |
| True peak | ≤ −3 dBTP; *flat factor* 0 |
| Piso de ruido (silencio inicial) | ≤ −60 dBFS y > −90 dBFS |
| Bordes | 0.2–0.6 s de silencio al inicio y al final |
| Pausas internas | Ninguna > 1 s |
| Espectrograma | Sibilantes hasta ≥18 kHz; sin líneas de 50/60 Hz; silencios limpios |
| Transcripción | Whisper sobre el clip = `.txt` (salvo puntuación) |
| Escucha | Sin clics de boca, respiraciones fuertes ni eco |

Solo los umbrales de RMS, pico y piso tienen fuente (ElevenLabs, ACX); el resto es criterio práctico.

---

## 8. Errores Comunes

| Error | Efecto | Cómo se detecta |
| :--- | :--- | :--- |
| Leer plano | Clon monótono | Escucha; rango de F0 bajo |
| Música o TV de fondo | Se clona o mete artefactos | Líneas armónicas en los silencios del espectrograma |
| Fuente comprimida | Techo de banda bajo 16 kHz | Espectrograma |
| Clipping | Distorsión que se copia | `astats`: pico ≥ −0.1 dB, *flat factor* > 0 |
| Variar la distancia | Timbre y nivel cambian (efecto de proximidad) | RMS por tramo muy dispar |
| Mezclar sesiones o salas | Estilos con timbre distinto | Comparar piso de ruido y espectro entre archivos |
| Pausas largas | Deriva y pausas raras en la salida | `silencedetect` > 1 s |
| Transcripción inexacta | Primera palabra trabada o palabras inventadas | Whisper sobre la referencia vs el `.txt` |
| Arranque lento en Chatterbox | El estilo sale del arranque | Revisar que los primeros 6 s ya tengan la actitud |
| Gate o denoise del celular, Zoom o Discord | Silencio digital (−inf), peor similitud | `astats`: piso −inf |

---

## 9. Ética y Consentimiento

* Clonar solo voces con permiso escrito de su dueño (ya en `AGENTS.md` y VoiceStudio).
* **Chatterbox marca todo audio con la marca de agua neural Perth** **(leída, README)**. En los otros cinco no se encontró marca incorporada (**no verificado**).
* El repo es **público**: las grabaciones `narration/voz/*.wav` no deben subirse. Hoy solo hay `.txt` versionados y el `.gitignore` ignora únicamente `narration/voz/prueba/`: **un `narration/voz/neutral.wav` quedaría versionable** (verificado con `git check-ignore` en esta sesión). Conviene agregar `narration/voz/**/*.wav` al `.gitignore` antes de grabar.
* En publicidad, declarar el contenido sintético donde la plataforma lo exija (**no verificado** en esta sesión).
