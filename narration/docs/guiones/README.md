# Guiones para grabar las voces de referencia

Los seis motores (Qwen3-TTS, Chatterbox, OmniVoice, VoxCPM2, IndexTTS 2.5 y CosyVoice 3) **copian timbre, ritmo, entonación, emoción, acento y sala** de la referencia. Lo que grabes aquí es literalmente cómo va a sonar toda la narración: una referencia apurada, con eco o con acento regional produce narraciones apuradas, con eco o con ese acento. La investigación completa está en [docs/research/voicestudio-narracion/11-audio-de-referencia.md](../../../docs/research/voicestudio-narracion/11-audio-de-referencia.md).

## El kit: 12 clips en una sola sesión

Se graba **un clip por estilo**, todos el mismo día, en el mismo lugar y con el micrófono en la misma posición. Grábalos **en este orden**: la neutral abre y cierra la sesión para comprobar que tu voz no cambió por cansancio.

| Orden | Archivo a grabar | Guion | Duración | Ritmo | Para qué videos |
|---|---|---|---|---|---|
| 1 | `narration/voz/neutral.wav` | [00-neutral.md](00-neutral.md) | 10–12 s | medio (~150 ppm) | Ancla de timbre; base para IndexTTS y VoxCPM2 con emoción por parámetro |
| 2 | `narration/voz/amistosa.wav` | [01-amistosa.md](01-amistosa.md) | 9–11 s | ágil (~165 ppm) | Reels, saludos, llamadas a la acción |
| 3 | `narration/voz/experta.wav` | [03-experta.md](03-experta.md) | 10–12 s | medio (~150 ppm) | Demos y tutoriales |
| 4 | `narration/voz/clara.wav` | [04-clara.md](04-clara.md) | 10–12 s | medio (~140 ppm) | Tutoriales paso a paso |
| 5 | `narration/voz/estable.wav` | [05-estable.md](05-estable.md) | 10–11 s | ágil (~160 ppm) | Corporativo, explicativos largos |
| 6 | `narration/voz/suave.wav` | [02-suave.md](02-suave.md) | 10–11 s | medio (~140 ppm) | Bienestar, temas sensibles |
| 7 | `narration/voz/energica.wav` | [06-energica.md](06-energica.md) | 8–10 s | rápido (~175 ppm) | Publicidad, ganchos de reel |
| 8 | `narration/voz/dramatica.wav` | [07-dramatica.md](07-dramatica.md) | 10–12 s | lento (~130 ppm) | Storytelling, tráiler |
| 9 | `narration/voz/triste.wav` | [08-triste.md](08-triste.md) | 10–12 s | lento (~120 ppm) | Historias emotivas |
| 10 | `narration/voz/intima.wav` | [09-intima.md](09-intima.md) | 9–11 s | lento (~125 ppm) | Secretos, cierres cercanos, suspenso |
| 11 | `narration/voz/neutral-en.wav` | [10-neutral-en.md](10-neutral-en.md) | 10–12 s | medio (~150 ppm) | **Videos en inglés** (evita el acento cruzado) |
| 12 | `narration/voz/neutral-fin.wav` | [00-neutral.md](00-neutral.md) (mismo texto) | 10–12 s | medio (~150 ppm) | Control de la sesión; también sirve de segunda neutral |
| Opc. | `narration/voz/susurro.wav` | [09-intima.md](09-intima.md#variante-susurro) | 7–9 s | lento | Solo efectos; pierde timbre |
| Opc. | `narration/voz/emociones/*.wav` | [11-emociones.md](11-emociones.md) | 5–8 s c/u | — | Clips de emoción para IndexTTS 2.5 (`emo_audio_prompt`) |

ppm = palabras por minuto.

**Por qué 8–12 s y no más:** Chatterbox toma el estilo solo de los **primeros 6 s** y el timbre de los primeros 10 s; OmniVoice rinde mejor con 3–10 s; IndexTTS corta a 15 s; CosyVoice rechaza más de 30 s. Un clip de 8–12 s sirve a los seis. **La actitud del estilo tiene que estar desde la primera palabra**: nada de arranques tibios.

## Equipo y técnica

- **Lugar**: un cuarto chico con ropa, cortinas o un sillón, que absorben el eco (un clóset con ropa funciona muy bien). Evita cocinas y baños. Apaga el ventilador, el aire acondicionado y aleja el refrigerador. **El modelo copia la sala**: una sala con eco clona con eco.
- **Micrófono**: a **10–20 cm** de la boca, un poco de costado para que las "p" no golpeen, y **a la misma distancia en todas las tomas** (marca la posición con cinta). En una sala sin tratar, un micrófono dinámico rechaza mejor la habitación; un celular sirve si la sala es seca.
- **Nivel**: los picos de la grabación entre **-12 y -6 dB**, nunca saturados. **No cambies la ganancia entre estilos**: la diferencia de volumen entre `intima` y `energica` es parte de la emoción y se normaliza después.
- **Formato**: **WAV mono, 48 kHz, 24 bits** (16 bits también sirve). Nada de m4a, mp3 ni audios de WhatsApp: la compresión se clona y convertir a WAV no la recupera.
- **Sin procesado**: sin compresor, sin ecualizador, sin reducción de ruido, sin "mejorar voz" del celular ni de Zoom. **El denoise baja la similitud con tu voz**: si hay ruido, vuelve a grabar.
- **Bordes**: deja **0.3–0.5 s de silencio** al inicio y al final. Ninguna pausa interna de más de 1 s.
- **Cuerpo**: de pie o sentado derecho, con agua sin gas a mano. Evita lácteos y café justo antes (ruidos de boca). Calienta 5 minutos leyendo todos los guiones en voz alta.

## Notación de los guiones

| Marca | Significa |
|---|---|
| `/` | Pausa corta (~0.3 s): una respiración mínima, sin cortar la idea |
| `//` | Pausa larga (~0.7 s): cambio de idea; aquí se respira |
| **negrita** | Palabra con énfasis: un poco más de intensidad y duración, **sin gritar** |
| ↗ | La entonación sube al final: pregunta de sí o no, o el **penúltimo** elemento de una lista con "y" |
| ↘ | La entonación baja al final: cierre, afirmación, o el **último** elemento de una lista con "y" |
| → | La entonación queda casi nivelada: elementos intermedios de una lista o frase que continúa |
| `[sonrisa]`, `[calma]`... | Actitud para esa frase. **No se lee** |

Las marcas **no se leen**. En una lista con "y" ("ideas, proyectos y notas"), el elemento antes de la "y" sube un poco y el último cae: así suena el español cuando cierra una enumeración.

El texto que dices tiene que coincidir **palabra por palabra** con `narration/voz/<estilo>.txt`. Si cambias algo al leer, edita el `.txt`. Qwen, CosyVoice (zero-shot) y VoxCPM2 (modo Hi-Fi) usan esa transcripción: si no coincide, **clonan peor y pueden trabar la primera palabra**.

## Español neutro: reglas para todas las grabaciones

1. **Seseo**: "c", "z" y "s" suenan igual. *Edición*, *organizo* y *sistema* llevan todas la misma "s".
2. **"S" final completa**: *ideas*, *proyectos*, *notas*. No la aspires ("ideah") ni la elimines.
3. **"D" entre vocales**: *ordenado*, *cuidado*, *pasado*. Nunca "ordenao".
4. **"LL" y "Y" suaves**: *proyectos*, *llegó*, *ya*. Ni "sh" ni "zh".
5. **"J" y "G" suaves**: *corrijo*, *gente*, *elige*. Sin raspar la garganta.
6. **"R" y "RR" vibrantes y limpias**: *pero* (simple), *corrijo*, *carta* (múltiple o vibrante clara).
7. **"Para" completo**, nunca "pa". Tampoco "pa'l" ni "'tá".
8. **Entonación plana de doblaje latino**: sin cantadito mexicano, colombiano, chileno ni rioplatense. Las subidas y bajadas son las que marca el guion, nada más.
9. **Nombres propios o de marca**: si un texto los trae, pronúncialos siempre igual en todas las tomas. El modelo copia lo que hagas.

## Cómo grabar cada clip

Con el comando del repo, que aplica la mayoría de estos pasos y verifica el resultado: `python narration/grabar.py --dispositivo <fuente> --estilo <estilo>` (ver [README §5](../../README.md#5-grabar-las-referencias)).


1. Lee la sección **Actitud** del guion y repasa la versión marcada en voz alta una vez.
2. Graba **3 tomas seguidas**, con 2 s de silencio entre ellas.
3. Escúchalas con audífonos y quédate con la que suene **más natural**, no con la más "actuada": una referencia sobreactuada hace que **toda** la narración suene sobreactuada.
4. Recórtala dejando 0.3–0.5 s de silencio en cada borde y guárdala como `narration/voz/<estilo>.wav`.
5. Verifica la duración y los niveles (abajo). Si quedó fuera de rango, el ritmo no es el pedido: repite.

## Convertir, recortar y normalizar con ffmpeg

```bash
# Recortar una toma (desde 4.2 s, durante 10.5 s) a WAV mono 48 kHz 24 bits
ffmpeg -ss 4.2 -t 10.5 -i sesion.wav -ac 1 -ar 48000 -c:a pcm_s24le narration/voz/bruto-amistosa.wav

# Normalizar con ganancia lineal (no cambia la dinámica) a -18 LUFS y pico real <= -3 dB
ffmpeg -i narration/voz/bruto-amistosa.wav -af loudnorm=I=-18:TP=-3:LRA=11:linear=true \
  -ac 1 -ar 48000 -c:a pcm_s24le narration/voz/amistosa.wav
```

Si `loudnorm` avisa que no puede quedarse en modo lineal, la toma tiene picos demasiado altos: aléjate un poco del micrófono y vuelve a grabar.

## Verificar cada clip

```bash
f=narration/voz/amistosa.wav
# Duración, canales y sample rate
ffprobe -v error -show_entries stream=channels,sample_rate:format=duration -of default=nw=1 "$f"
# Loudness y pico real
ffmpeg -hide_banner -nostats -i "$f" -af ebur128=peak=true -f null - 2>&1 | tail -n 12
# Piso de ruido (los primeros 0.3 s deben ser silencio)
ffmpeg -hide_banner -nostats -t 0.3 -i "$f" -af astats=measure_perchannel=none:measure_overall=RMS_level -f null - 2>&1 | grep RMS
# Pausas internas largas (no debería aparecer ninguna de más de 1 s salvo los bordes)
ffmpeg -hide_banner -nostats -i "$f" -af silencedetect=n=-45dB:d=0.25 -f null - 2>&1 | grep silence_
```

| Check | Aprobado |
|---|---|
| Duración | La del guion (8–12 s) |
| Formato | 1 canal, 48 kHz |
| Loudness integrada | -20 a -16 LUFS |
| Pico real | ≤ -3 dBTP |
| Piso de ruido (silencio inicial) | ≤ -60 dB y > -90 dB (más bajo indica un "gate" o silencio digital) |
| Pausas internas | Ninguna de más de 1 s |
| Transcripción | Whisper sobre el clip dice lo mismo que el `.txt` |
| Escucha con audífonos | Sin eco, clics de boca, respiraciones fuertes ni ruido de fondo |

## Probar la referencia

```bash
python narration/tts.py --modelo qwen-0.6b --estilo amistosa \
  --texto "Hola, ¿cómo estás? Hoy te muestro cómo editar un video en menos de un minuto."
```

Compara la salida (`out/narration/qwen-0.6b-amistosa.wav`) con tu grabación. Si se oye un acento que no es el tuyo, revisa los puntos 1 a 8. Si el ritmo no se parece, vuelve a grabar respetando las pausas. Cuando estén los motores nuevos, repite la prueba con cada uno ([spec](../../../docs/specs/narracion-motores-voicestudio.md)).

## Checklist final

- [ ] 12 archivos en `narration/voz/`: `neutral`, `amistosa`, `experta`, `clara`, `estable`, `suave`, `energica`, `dramatica`, `triste`, `intima`, `neutral-en` y `neutral-fin` (`.wav`).
- [ ] Cada `.wav` dice exactamente lo de su `.txt`.
- [ ] Todos grabados en la misma sesión, lugar, micrófono, distancia y ganancia.
- [ ] Mono, 48 kHz, sin eco, sin ruido de fondo, sin saturar, sin procesar.
- [ ] Duraciones y niveles dentro de los rangos.
- [ ] `neutral.wav` y `neutral-fin.wav` suenan a la misma voz.
- [ ] Los `.wav` **no** se suben al repo: `.gitignore` ignora `narration/voz/**/*.wav` (el repo es público).
- [ ] La persona que graba dio permiso para clonar su voz.
