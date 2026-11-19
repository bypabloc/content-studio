# 11 · Clips de emoción (opcional) → `server/data/narration/reference/emotions/<emocion>.wav`

**Intención**: clips cortos con una emoción marcada, para que **IndexTTS 2.5** la copie sobre el timbre de `neutral.wav` (`emo_audio_prompt`).
**Duración objetivo**: 5–8 s cada uno · **Orden en la sesión**: después de `neutral-en.wav` y antes de `neutral-end.wav`

## Para qué sirve

IndexTTS separa **timbre** (la referencia) y **emoción** (otro clip). Con estos clips, cualquier guion puede sonar alegre, triste o tenso con tu voz, sin grabar una referencia completa por emoción. También sirven de comparación para el vector de emociones, que no necesita grabación. **No llevan `.txt`**: IndexTTS no usa la transcripción del clip de emoción.

Puedes **exagerar un poco más** que en las referencias de estilo: aquí la emoción es lo único que importa, y el motor la mezcla con un peso (`emo_alpha`) que se ajusta después.

## Los clips

| Archivo | Emoción | Texto | Cómo decirlo |
|---|---|---|---|
| `alegria.wav` | Alegría | ¡No lo puedo creer, salió perfecto! Mira esto, de verdad me encanta. | Sonrisa amplia, tono alto, ritmo vivo |
| `tristeza.wav` | Tristeza | Ya no está… Y todavía me cuesta entender cómo pasó. | Lento, voz baja, frases que caen |
| `enojo.wav` | Enojo contenido | Te lo dije tres veces. No es tan difícil hacerlo bien. | Firme, cortante, sin gritar |
| `miedo.wav` | Miedo y tensión | Espera… ¿escuchaste eso? Hay alguien afuera. | Contenido, rápido, respiración corta |
| `sorpresa.wav` | Sorpresa | ¿En serio? ¿Todo esto lo hiciste tú solo? | Tono que sube, asombro genuino |
| `calma.wav` | Calma | Tranquilo, todo va a estar bien. Vamos paso a paso. | Lento, grave y cálido |

## Cuidado con

- Una emoción por clip: no mezcles sorpresa y alegría en el mismo.
- Misma distancia y ganancia que el resto de la sesión.
- Los clips de emoción pueden ser de otra persona (IndexTTS conserva tu timbre), pero si son tuyos el resultado es más coherente.
