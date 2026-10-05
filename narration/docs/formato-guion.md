# Formato del guion para `tts.py`

Cómo escribir el texto que se pasa con `--texto` o `--archivo` para controlar pausas, entonación y pronunciación.

> **Alcance:** medido el 4 de octubre de 2026 con **Qwen3-TTS 0.6B Base** y una referencia en estilo `experta`. Con `qwen-1.7b` el comportamiento debería ser parecido. Con `chatterbox` no se midió.

## Resumen

- Escribe **texto plano**. No hay etiquetas, SSML ni marcas especiales.
- **La puntuación es el único control**, y es aproximado.
- **Las tildes son obligatorias**. Sin ellas, el modelo cambia la sílaba tónica.
- Escribe **números, siglas y símbolos como se pronuncian**.
- **Los respiros y el énfasis no se pueden pedir.** Salen de la grabación de referencia.

## Por qué no hay marcas

El modelo Base (el que clona voz) recibe el texto tal cual, dentro de su plantilla de chat (`<|im_start|>assistant\n{texto}<|im_end|>`). No lo normaliza ni interpreta etiquetas. Tampoco acepta instrucciones de estilo: el parámetro `instruct` solo existe en CustomVoice y VoiceDesign, que no clonan voz.

Las etiquetas que circulan en guías de internet (`[gasp]`, `[sighing]`, `[whispers]`…) son de la API en la nube de Qwen, no de los modelos abiertos.

**Lo que pasa si las usas** (todas se pronuncian en voz alta):

| Escrito | Lo que dijo el modelo |
|---|---|
| `[breath]` | "Braids" |
| `[pause]` | "pause" |
| `<break time="1s"/>` | "Break Time" |
| `(pausa)` | "pausa" |
| `**editor**` | "editor-editor" |
| `EDITOR` en mayúsculas | Sin énfasis ni cambio |

Tampoco uses la notación de [guiones/](guiones/README.md) (`/`, `//`, `↗`, `[sonrisa]`). Sirve solo para grabar las referencias.

## Pausas

Pausa medida después de una palabra en mitad de la oración. Es la mediana de 4 generaciones con semillas distintas, porque el modelo muestrea al azar y la misma frase no sale igual dos veces.

| Signo | Pausa mediana | Fiabilidad |
|---|---|---|
| ninguno | 0 s | — |
| `,` | 0.30 s | Estable (0.19–0.55 s) |
| `—` | 0.42 s | Estable (0.17–0.57 s) |
| `...` o `…` | 0.52 s | **La más estable** (0.38–0.72 s) |
| `;` | 0.56 s | Errática: entre 0 y 1.07 s |
| `:` | 0.64 s | Errática: entre 0 y 1.12 s |
| varios espacios | ~0.1 s | Sin efecto útil |

- El **punto** separa bien oraciones normales (~0.5–1 s), pero después de una oración muy corta ("Abre el editor.") la pausa fue inconsistente.
- **Los saltos de línea y las líneas en blanco no sirven**: `tts.py` junta todo el texto en una sola línea antes de enviarlo.
- **Entre bloques** (cada ~300 caracteres) `tts.py` agrega 0.25 s fijos de silencio.

**Regla práctica:** `,` para una pausa corta, `…` para una media y `.` para cerrar una idea. Hoy no hay forma confiable de pedir una pausa larga ni de fijar su duración exacta.

## Entonación

- `¿…?` sube la entonación al final y `¡…!` le da más energía. Pon los dos signos, el de apertura y el de cierre.
- Una oración larga sin puntuación se lee con un ritmo plano y continuo. Corta las ideas con comas o puntos.

## Pronunciación

- **Tildes:** sin tilde, "Hoy termino el guion" se leyó "Hoy terminó el guío". El modelo se guía por la tilde para decidir la sílaba tónica.
- **Números:** escríbelos en letras ("quince", "dos mil veintiséis", "cincuenta por ciento"). Con dígitos no se pudo confirmar que la lectura sea correcta en español.
- **Siglas y palabras en inglés:** escríbelas como suenan ("u ere ele", "yutuber") si el modelo las pronuncia mal. Mantén la misma grafía en todo el guion.

## Respiros y énfasis

No se pueden indicar en el texto. El modelo copia la manera de hablar de la referencia (ritmo, respiraciones, intensidad), así que para obtener otro resultado hay que cambiar la grabación. Ver [guiones/](guiones/README.md).

## Ejemplo

```text
Hola, bienvenidos al canal. Hoy te muestro cómo editar un video en menos de un minuto.
Primero, abre el editor… y arrastra tu clip a la línea de tiempo.
¿Quieres el truco final? Quédate hasta el final, porque vale la pena.
```

## Fuentes

- Código de `qwen_tts`: `inference/qwen3_tts_model.py`, funciones `_build_assistant_text` y `generate_voice_clone`.
- [Discusión #75 de Qwen3-TTS: add a pause in a sentence](https://github.com/QwenLM/Qwen3-TTS/discussions/75). Ahí se reporta que `\n`, `...` y `-` "no hacen diferencia" y que varios espacios entre comillas generan pausas. En nuestras pruebas, los puntos suspensivos sí funcionaron y los espacios no.
- [Qwen3 TTS Prompt Guide](https://www.qwen3tts.net/qwen3-tts-prompt-guide): sitio no oficial; sus etiquetas son de la API en la nube.
