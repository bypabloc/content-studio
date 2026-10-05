# Formato del guion para `tts.py`

Cómo escribir el texto que se pasa con `--texto` o `--archivo` para controlar pausas, entonación y pronunciación.

> **Alcance:** medido el 4 de octubre de 2026 con **Qwen3-TTS 0.6B Base** y una referencia en estilo `experta`. Con `qwen-1.7b` el comportamiento debería ser parecido. Con `chatterbox` solo se midieron las pausas largas (ver abajo); los signos y las etiquetas no.

## Resumen

- Escribe **texto plano**. El modelo no entiende etiquetas, SSML ni marcas especiales.
- **La puntuación controla las pausas cortas**, de forma aproximada.
- **Para pausas largas** usa una línea en blanco (0.6 s) o `[pausa N]` (N segundos). Las inserta `tts.py`, no el modelo.
- **Las tildes son obligatorias**. Sin ellas, el modelo cambia la sílaba tónica.
- Escribe **números, siglas y símbolos como se pronuncian**.
- **Los respiros y el énfasis no se pueden pedir.** Salen de la grabación de referencia.
- **Todas las reglas de la sección siguiente son obligatorias.**

## Reglas obligatorias

**Todo guion tiene que cumplir todas estas reglas.** No son sugerencias: salen de las pruebas que se detallan en las secciones de abajo. Las cifras que no salen de una medición (el máximo de `…` y el largo de las oraciones) se marcan como *criterio*. Un guion que no las cumpla se corrige antes de generar el audio. Antes de generar, `tts.py` solo avisa de las etiquetas (regla 1); el resto lo revisa quien escribe el guion. Después de generar, `--evaluar` detecta las palabras que el modelo dijo mal y los silencios fuera de lugar (regla 24).

**Marcas** ([Por qué no hay marcas](#por-qué-no-hay-marcas))

1. Ninguna etiqueta ni marca: nada de `[…]` (salvo `[pausa N]`), `<…>`, `**`, `(pausa)` ni la notación de grabación (`/`, `//`, `↗`, `↘`, `→`, `[curiosa]`).
2. Nada de mayúsculas para dar énfasis: no cambian nada. "DEMO" se escribe "demo".

**Pausas** ([Pausas](#pausas))

3. Toda oración termina en `.`, `?` o `!`.
4. `,` para las pausas cortas: entre los elementos de una enumeración y antes de "y" o "pero" cuando unen dos ideas.
5. `…` una o dos veces por guion, en la frase que más importa (*criterio*: con más, la voz suena dudosa).
6. Nada de `;`: se cambia por `.`. El `:` solo antes de una enumeración ("tu historial completo: consultas, antecedentes…"). En los demás casos, `.`.

**Pausas largas** ([Pausas largas](#pausas-largas))

7. Una idea por párrafo: separados por una línea en blanco o, en JSON, un elemento de `texto` por idea.
8. `[pausa 1]` después del gancho (la primera frase).
9. `[pausa 0.8]` antes del cierre (la llamada a la acción).

   Las dos van al final de la línea: `"¿Alguna vez buscaste la ficha de un paciente… y no apareció? [pausa 1]"`. Los valores 1 s y 0.8 s son un punto de partida: las pausas sí se midieron, pero no se comparó al oído qué duración funciona mejor.

**Entonación** ([Entonación](#entonación))

10. Toda pregunta lleva `¿…?` y toda exclamación `¡…!`, siempre con los dos signos. Sin el de apertura, el modelo no anticipa la entonación.
11. Oraciones de 25 palabras como máximo (*criterio*). Una oración larga sin puntuación se lee con un ritmo plano.

**Pronunciación** ([Pronunciación](#pronunciación))

12. Tildes correctas en todas las palabras.
13. Números en letras: "veinticuatro horas", no "24 horas".
14. Siglas deletreadas: "pe de efe", "cu erre", "a, be, ce, de, e".
15. Palabras en inglés escritas como se dicen: "guasap", "estok", "zum".
16. Marcas y nombres escritos como suenan, con tilde en la sílaba tónica: "Clinikái", "nunes".

**Palabras que el modelo pierde** ([Palabras que el modelo pierde](#palabras-que-el-modelo-pierde))

17. Un verbo terminado en "-s" no va seguido de una palabra que empieza con "s": las dos "s" se funden y se oye otra persona ("escribes su" → "escribe su"). Cambia el artículo o el orden: "escribes **la** cédula", "**solo activas**", "**siempre lo** encuentras".
18. Una palabra clave corta, como "demo", no va sola ni al final de un párrafo: "**Comenta la palabra demo, y te enviamos…**", no "¡Comenta demo!".
19. Evita "registras": el modelo la deforma casi siempre ("registra", "regista", "digitas"). Usa una construcción impersonal: "queda registrado".
20. Si un verbo en segunda persona sigue fallando ("eliges el diagnóstico", "recepción ve cuáles"), pasa la oración a impersonal: "el diagnóstico se elige con un clic" (de 1/5 a 4/5), "en recepción se ve cuáles están listas" (de 2/5 a 4/5).
21. Si un párrafo tiene dos oraciones, separa las oraciones con `[pausa 0.6]`: entre oraciones del mismo bloque, el modelo a veces deja silencios de 1.4 s. La marca va dentro de la misma línea, así que no corre la numeración de `visuales`.
22. La última palabra de un párrafo es la más frágil: en el 40–60 % de las generaciones cambia su vocal final ("cuenta" → "cuento", "parto" → "parte"). Si es una palabra que importa, no la dejes al final: agrega algo después ("cada segundo cuenta **mucho**", de 0/3 a 3/3) o reordena ("…, **inventario y pacientes nuevos**", no "…, pacientes nuevos e inventario", que falló en tres tandas seguidas).

**Proceso** ([Guiones en JSON](#guiones-en-json) y `--evaluar` en el [README](../README.md#evaluar-las-salidas---evaluar))

23. En un JSON con `visuales`, no cambies la cantidad de elementos de `texto`: cada `linea` de `visuales` apunta a uno. Para cortar dentro de una línea, usa `[pausa N]`.
24. Todo guion se genera con `--evaluar --reintentos 4`, y se lee el informe. Si un párrafo falla en **todas** las rondas, el problema es la escritura: corrígelo con las reglas 17 a 22 y vuelve a generar ese guion. Si falla solo a veces, es azar del muestreo y lo resuelven los reintentos.
25. Escucha lo que el evaluador no oye: la entonación, la pronunciación de la marca y los párrafos con aviso de ritmo.

### Ejemplo que cumple todas las reglas

```json
"texto": [
  "¿Alguna vez buscaste la ficha de un paciente… y no apareció? [pausa 1]",
  "Una carpeta extraviada es una historia clínica que se pierde, con todo lo que tenía adentro.",
  "En Clinikái escribes la cédula o el nombre y, en segundos, tienes el historial completo: consultas, antecedentes, alergias y documentos.",
  "Todo queda ordenado, en la nube y respaldado cada día.",
  "Desde el navegador, sin instalar nada, para el consultorio independiente y para la policlínica. [pausa 0.8]",
  "Comenta la palabra demo, y te enviamos un video corto de cómo funciona."
]
```

## Palabras que el modelo pierde

Medido con `--evaluar` y experimentos de 3 a 5 generaciones por variante (las variantes se transcribieron con whisper `medium`):

| Escritura | Bien | Escritura que la evita | Bien |
|---|---|---|---|
| "escribes su cédula… tienes su historial" | 1/5 | "escribes la cédula… tienes el historial" | 3/5 |
| "Activas solo las que atiendes" | 2/5 | "Solo activas las que atiendes" | 5/5 |
| "Y lo encuentras siempre" | 0/5 | "Y siempre lo encuentras" | 4/5 |
| "Lo abres, inicias sesión" | 1/5 | "Lo abres, entras" | — |
| "¡Comenta demo!" (párrafo propio) | 3/5 | "Comenta la palabra demo, y te enviamos…" | 20/20 |
| "Registras los signos vitales" | 0/5 | "Anotas los signos vitales" | 2/5 |
| "Registras los signos vitales… y eliges el diagnóstico" | 1/5 | "Los signos vitales quedan registrados… y el diagnóstico se elige con un clic" | 4/5 |
| "y recepción ve cuáles están listas" | 2/5 | "y en recepción se ve cuáles están listas" | 4/5 |
| "…cada segundo cuenta." (final del párrafo) | 0/3 | "…cada segundo cuenta mucho." | 3/3 |
| "…pacientes nuevos e inventario." | falló 3 tandas | "…inventario y pacientes nuevos." | bien en la tanda siguiente |

**Lo que no se arregla escribiendo.** La última palabra de un párrafo a veces cambia de vocal ("parto" → "parte", en el 40–60 % de las generaciones), y "gestacional" se oye a veces "estacional". Probé con temperaturas 0.5, 0.6 y 0.8 y no mejoró de forma consistente. Es azar del muestreo, así que la solución es regenerar ese párrafo: `--evaluar --reintentos 4` lo hace solo. Con los 22 guiones de prueba, ya corregidos con estas reglas, las rondas regeneraron 40 → 15 → 8 → 5 párrafos.

**Lo que no es un error del audio.** Cuando una "s" final se junta con otra inicial, se oye una sola "s" y la frase es ambigua para cualquiera: whisper oyó "eres tú quien **decides** si" en 5 de 5 generaciones de "eres tú quien **decide** si". "Tú decides si incluir" salió bien en 4 de 5, así que se puede dejar. Las listas ("medicina general, odontología, pediatría…") se leen más lento a propósito, unas 2 palabras/s contra 3.3 de mediana; por eso el ritmo es solo un aviso.

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

`tts.py` muestra un aviso antes de generar si el texto tiene `[…]`, `<…>`, `**` o `(pausa)`. La única excepción es `[pausa N]` (ver más abajo).

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
- **Un salto de línea simple no hace nada**: se une con la línea siguiente.
- **Entre bloques** (cada ~300 caracteres) `tts.py` agrega 0.25 s fijos de silencio.

**Regla práctica:** `,` para una pausa corta, `…` para una media y `.` para cerrar una idea. **Evita el `;`**: cámbialo por un punto ("Tú revisas y decides. El sistema solo calcula."). Los `:` antes de una enumeración pueden quedarse.

### Pausas largas

El modelo no puede hacer pausas largas de forma confiable, así que `tts.py` corta el texto en esos puntos y agrega silencio real:

| Escribe | Silencio insertado | Medido con Qwen | Medido con Chatterbox |
|---|---|---|---|
| Una línea en blanco entre párrafos | 0.6 s | 0.90 s | 0.85 s |
| `[pausa N]` (también `[pausa 1,5]` o `[pausa 2s]`) | N s | 2.28 s con N = 2 | 1.87 s con N = 1.5 |

La diferencia, unos 0.3 s, es la caída natural de la voz más un margen de 0.08 s que se deja a cada lado del bloque para no cortar consonantes. El modelo deja además unos 0.5 s de silencio en cada borde de bloque; `tts.py` los recorta, porque si no las pausas se alargaban más de 1 s.

- Si entre dos párrafos hay una `[pausa N]`, manda la marca y la línea en blanco no suma. Varias marcas seguidas se suman.
- Una `[pausa N]` al final del texto deja ese silencio al final del audio. Al principio del texto no tiene efecto.
- El silencio se acelera junto con el audio en los estilos con velocidad distinta de 1 (`amistosa` y `estable`, ×1.05; `clara`, ×0.97).
- Cada corte termina un bloque. Antes de una pausa, cierra la idea con `.`, `?` o `!` para que la entonación baje bien.

## Entonación

- `¿…?` sube la entonación al final y `¡…!` le da más energía. Pon los dos signos, el de apertura y el de cierre.
- Una oración larga sin puntuación se lee con un ritmo plano y continuo. Corta las ideas con comas o puntos.
- Las enumeraciones se leen más despacio que el resto (medido: ~2 palabras/s contra 3.3). Es esperable; si te parece lento al escucharlo, acórtala.

## Pronunciación

- **Tildes:** sin tilde, "Hoy termino el guion" se leyó "Hoy terminó el guío". El modelo se guía por la tilde para decidir la sílaba tónica.
- **Números:** escríbelos en letras ("quince", "dos mil veintiséis", "cincuenta por ciento"). Con dígitos no se pudo confirmar que la lectura sea correcta en español.
- **Siglas:** deletréalas como se pronuncian. Tal cual, el modelo las lee como le parece. "criterios ABCDE" se oyó "criterios A, B, C, D" (sin la E), y deletreada salió completa.

  | En pantalla | En el guion |
  |---|---|
  | PDF | pe de efe |
  | QR | cu erre |
  | IMC | i eme ce |
  | OMS | o eme ese |
  | ABCDE | a, be, ce, de, e |

- **Palabras en inglés:** escríbelas como se dicen en español: "WhatsApp" → "guasap", "stock" → "estok", "zoom" → "zum".
- **Marcas y nombres inventados:** escríbelos como suenan, con tilde en la sílaba tónica. "Klinikae" se oyó "ClaniKey"; escrito "Clinikái" sale bien. Lo mismo con palabras escritas a propósito de forma rara: "Escribe nunez" se oyó "Escribe en un es", y "nunes" salió bien.
- Esa grafía es **solo para la narración**. En pantalla y en las publicaciones va la escritura real.
- Una palabra en mayúsculas (DEMO) no cambia nada: escríbela en minúscula.

## Respiros y énfasis

No se pueden indicar en el texto. El modelo copia la manera de hablar de la referencia (ritmo, respiraciones, intensidad), así que para obtener otro resultado hay que cambiar la grabación. Ver [guiones/](guiones/README.md).

## Ejemplo

```text
¿Te toma horas editar un video? [pausa 1]

Hoy te muestro cómo hacerlo en menos de un minuto.

Primero, abre el editor… y arrastra tu clip a la línea de tiempo.

Después, elige la resolución y exporta el video. [pausa 0.8]

Comenta guía y te la enviamos completa.
```

Hay 1 s de silencio después del gancho, 0.6 s entre los párrafos (líneas en blanco) y 0.8 s antes del cierre.

## Guiones en JSON

Para generar varios guiones de una vez, cada uno puede ir en un `.json`:

```json
{
  "id": "011-nunez-sin-tilde",
  "titulo": "Núñez sin tilde",
  "estilo": "amistosa",
  "texto": [
    "Escribe nunes, sin tilde ni eñe… y aparece Núñez. [pausa 1]",
    "En Clinikái buscas por nombre o por cédula, y encuentras al paciente. [pausa 0.8]",
    "Comenta demo y te enviamos un video corto de cómo funciona."
  ]
}
```

| Campo | Uso |
|---|---|
| `texto` | Lista de párrafos, con las mismas reglas de este documento. Entre párrafos hay una pausa como la de una línea en blanco (0.6 s). También acepta un solo string |
| `estilo` | `amistosa`, `suave`, `experta`, `clara` o `estable`. Elige la grabación de referencia de todo el guion. `--estilo` en la línea de comandos lo reemplaza |
| `id` | Nombre del archivo de salida: `<id>-<modelo>.wav`. Si falta, se usa el nombre del `.json` |
| otros (`titulo`, `idioma`…) | `tts.py` los ignora |

Las marcas de actitud de la notación de grabación (`[curiosa]`, `[animada]`) no sirven aquí: el modelo las lee en voz alta. El tono sale del `estilo`.

```bash
# Varios guiones en una corrida: el modelo se carga una sola vez
python narration/tts.py --modelo qwen-0.6b --archivo guiones/*.json --salida out/narration/organic
```

Medido con 3 guiones (unos 30 s de audio cada uno): el primero tardó 28.8 s con la carga del modelo incluida, y los siguientes 21.9 s y 18.7 s.

## Fuentes

- Código de `qwen_tts`: `inference/qwen3_tts_model.py`, funciones `_build_assistant_text` y `generate_voice_clone`.
- [Discusión #75 de Qwen3-TTS: add a pause in a sentence](https://github.com/QwenLM/Qwen3-TTS/discussions/75). Ahí se reporta que `\n`, `...` y `-` "no hacen diferencia" y que varios espacios entre comillas generan pausas. En nuestras pruebas, los puntos suspensivos sí funcionaron y los espacios no.
- [Qwen3 TTS Prompt Guide](https://www.qwen3tts.net/qwen3-tts-prompt-guide): sitio no oficial; sus etiquetas son de la API en la nube.
