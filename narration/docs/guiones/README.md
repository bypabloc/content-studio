# Guiones para grabar las voces de referencia

Qwen3-TTS y Chatterbox **copian timbre, ritmo, entonación y acento** de la referencia. Lo que grabes aquí es literalmente cómo va a sonar toda la narración: una referencia apurada, con eco o con acento regional produce narraciones apuradas, con eco o con ese acento.

Se graba **una referencia por estilo**:

| # | Archivo a grabar | Guion | Duración objetivo | Ritmo |
|---|---|---|---|---|
| 1 | `narration/voz/amistosa.wav` | [01-amistosa.md](01-amistosa.md) | 11–13 s | ágil (~165 ppm) |
| 2 | `narration/voz/suave.wav` | [02-suave.md](02-suave.md) | 14–16 s | medio (~140 ppm) |
| 3 | `narration/voz/experta.wav` | [03-experta.md](03-experta.md) | 15–17 s | medio (~150 ppm) |
| 4 | `narration/voz/clara.wav` | [04-clara.md](04-clara.md) | 14–16 s | medio (~140 ppm) |
| 5 | `narration/voz/estable.wav` | [05-estable.md](05-estable.md) | 11–13 s | ágil (~160 ppm) |

ppm = palabras por minuto.

## Notación de los guiones

| Marca | Significa |
|---|---|
| `/` | Pausa corta (~0.3 s): una respiración mínima, sin cortar la idea |
| `//` | Pausa larga (~0.7 s): cambio de idea; aquí se respira |
| **negrita** | Palabra con énfasis: un poco más de intensidad y duración, **sin gritar** |
| ↗ | La entonación sube al final (pregunta, invitación) |
| ↘ | La entonación baja al final (cierre, afirmación) |
| → | La entonación queda suspendida (enumeración que continúa) |
| `[sonrisa]`, `[calma]`... | Actitud para esa frase. **No se lee** |

Las marcas **no se leen**. El texto que dices tiene que coincidir **palabra por palabra** con `narration/voz/<estilo>.txt`. Si cambias algo al leer, edita el `.txt`; Qwen falla si no coinciden.

## Español neutro: reglas para las cinco grabaciones

1. **Seseo**: "c", "z" y "s" suenan igual. *Edición*, *selecciona* y *sistema* llevan todas la misma "s".
2. **"S" final completa**: *ideas*, *proyectos*, *notas*. No la aspires ("ideah") ni la elimines.
3. **"D" entre vocales**: *ordenado*, *diseñado*, *registrada*. Nunca "ordenao".
4. **"LL" y "Y" suaves**: *proyectos*, *luego*, *ya*. Ni "sh" ni "zh".
5. **"J" y "G" suaves**: *dejar*, *registro*, *agenda*. Sin raspar la garganta.
6. **"R" y "RR" vibrantes y limpias**: *registro*, *real*, *grabación*.
7. **"Para" completo**, nunca "pa". Tampoco "pa'l" ni "'tá".
8. **Entonación plana de doblaje latino**: sin cantadito mexicano, colombiano, chileno ni rioplatense. Las subidas y bajadas son las que marca el guion, nada más.
9. **Nombres propios o de marca**: si un texto los trae, pronúncialos siempre igual en todas las tomas. El modelo copia lo que hagas.

## Antes de grabar

- **Lugar**: un cuarto chico con ropa, cortinas o un sillón, que absorben el eco. Evita cocinas y baños. Apaga el ventilador y el aire acondicionado.
- **Micrófono**: a 15–20 cm de la boca, un poco de costado para que las "p" no golpeen. Un celular sirve; un micrófono USB o de solapa es mejor.
- **Nivel**: los picos deben quedar entre -12 y -6 dB, nunca saturados. Si el programa muestra rojo, aléjate.
- **Cuerpo**: grábalo de pie o sentado derecho y con agua a mano. Calienta la voz leyendo el guion completo dos veces antes de grabar.
- **Formato**: WAV mono a 44.1 o 48 kHz. Si tu grabadora solo da m4a o mp3, conviértelo (ver abajo).
- Deja **medio segundo de silencio** al inicio y al final, sin respiraciones fuertes ni clics de mouse.

## Cómo grabar cada estilo

1. Lee la sección **Actitud** del guion y repasa la versión marcada en voz alta una vez.
2. Graba **3 tomas seguidas**, con 2 s de silencio entre ellas.
3. Escúchalas con audífonos y quédate con la que suene **más natural**, no con la más "actuada".
4. Recórtala y guárdala como `narration/voz/<estilo>.wav`.
5. Verifica que la duración esté en el rango de la tabla. Si quedó muy por fuera, el ritmo no es el pedido.

## Convertir y recortar con ffmpeg

```bash
# m4a/mp3 a WAV mono a 48 kHz
ffmpeg -i grabacion.m4a -ac 1 -ar 48000 narration/voz/amistosa.wav

# Recortar una toma (desde 4.2 s, durante 12.5 s)
ffmpeg -ss 4.2 -t 12.5 -i grabacion.m4a -ac 1 -ar 48000 narration/voz/amistosa.wav

# Ver la duración
ffprobe -v error -show_entries format=duration -of csv=p=0 narration/voz/amistosa.wav
```

## Probar la referencia

```bash
python narration/tts.py --modelo qwen-0.6b --estilo amistosa \
  --texto "Hola, ¿cómo estás? Hoy te muestro cómo editar un video en menos de un minuto."
```

Compara la salida (`out/narration/qwen-0.6b-amistosa.wav`) con tu grabación. Si se oye un acento que no es el tuyo, revisa los puntos 1 a 8. Si el ritmo no se parece, vuelve a grabar respetando las pausas.

## Checklist final

- [ ] 5 archivos en `narration/voz/`: `amistosa.wav`, `suave.wav`, `experta.wav`, `clara.wav` y `estable.wav`.
- [ ] Cada `.wav` dice exactamente lo de su `.txt`.
- [ ] Mono, sin eco, sin ruido de fondo, sin saturar.
- [ ] Duraciones dentro del rango de la tabla.
- [ ] Una sola voz (la misma persona) en las cinco, salvo que quieras voces distintas por estilo.
- [ ] La persona que graba dio permiso para clonar su voz.
