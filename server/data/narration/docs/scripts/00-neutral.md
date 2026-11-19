# 0 · Neutral → `server/data/narration/voz/neutral.wav` y `server/data/narration/voz/neutral-fin.wav`

**Intención**: tu voz natural, sin estilo; ritmo medio. Es el **ancla de timbre** de todo el kit.
**Duración objetivo**: 10–12 s · **Ritmo**: medio (~150 ppm) · **Tono**: el de tu voz en reposo · **Orden en la sesión**: 1.º (`neutral.wav`) y último (`neutral-fin.wav`, mismo texto)

## Para qué sirve

- **IndexTTS 2.5** clona el timbre de este clip y le pone la emoción por parámetro (vector de emociones o clip de emoción).
- **VoxCPM2** en modo controlable: este clip da el timbre y una instrucción en inglés da el estilo.
- **Comparar motores**: la misma referencia neutral en los seis motores muestra cuál suena más a ti.
- **Control de la sesión**: `neutral-fin.wav` se graba al final con el mismo texto. Si suena distinto a `neutral.wav` (más ronca, más cansada), la sesión no fue pareja.

## Actitud

Hablas como cuando le cuentas a alguien qué hiciste en el día: ni animado ni serio. Sin sonrisa forzada, sin tono de locutor. Es la voz que usarías para dejar un mensaje de audio a un conocido.

## Versión marcada

> Hoy quiero contarte / cómo organizo mis proyectos del año. ↘ //
> Primero escribo la idea, / después la grabo con calma ↗ /
> y, al final, / corrijo cada detalle con mucho cuidado. ↘

## Frase por frase

| Frase | Cómo decirla |
|---|---|
| *Hoy quiero contarte cómo organizo mis proyectos del año.* | Natural, cierra bajando |
| *Primero escribo la idea, después la grabo con calma* | Dos pasos parejos; "calma" sube apenas porque viene un último paso |
| *y, al final, corrijo cada detalle con mucho cuidado.* | El cierre cae con seguridad |

## Rasgos del español neutro que cubre

| Rasgo | Palabras |
|---|---|
| Seseo (z = s) | *organizo* |
| "Y" suave | *proyectos* |
| Ñ | *año* |
| "RR" vibrante y "J" suave | *corrijo* |
| "D" entre vocales completa | *cuidado* |
| CH | *mucho* |
| "S" final completa | *mis*, *proyectos*, *después* |

## Cuidado con

- *corrijo*: "rr" vibrante y "j" suave, sin raspar.
- *cuidado*: nunca "cuidao".
- *después*: la "s" final completa.
- No lo leas: cuéntalo.

## Texto exacto (debe coincidir con `voz/neutral.txt` y `voz/neutral-fin.txt`)

```
Hoy quiero contarte cómo organizo mis proyectos del año. Primero escribo la idea, después la grabo con calma y, al final, corrijo cada detalle con mucho cuidado.
```
