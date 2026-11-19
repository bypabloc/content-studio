# 006: los avisos del editor se pintan en una capa detrás del campo, y el texto del aviso va en el tooltip

- **Contexto**: el AC-6 pide el `;` subrayado con el texto de la regla 6 como tooltip. Un campo HTML no puede subrayar parte de su texto, y el editor no necesita sintaxis (plan, D-5).
- **Elegida**: un `textarea` transparente encima de una capa con el mismo texto, donde cada aviso va en un `<mark>` con `title` y el mensaje que manda el server. El lint lo calcula el server (`POST /narration/lint`, con su texto ya en español), y el cliente solo ubica cada aviso por línea y columna (`markSegments`). La capa va en `aria-hidden`: lo que se lee es el campo. Los avisos se piden 300 ms después del último cambio.
- **Descartadas**: CodeMirror (pesa más y da una sintaxis que el guion no tiene); reglas del linter en TypeScript (dos fuentes de verdad, D-1); un tooltip propio (el `title` nativo ya sale en el WebView).
- **Cómo revertir**: quitar `ScriptHighlight` y la capa de `ScriptEditor`; el campo queda sin subrayado y los avisos siguen en el contador.
- **Cómo comprobarla**: `bun run --cwd client test` (`ScriptEditor.test.tsx`, AC-6; `ScriptHighlight.test.tsx`). En la verificación final (T9), la capa se alinea con el texto en la app real: con líneas largas y con el zoom.
