# 016: arrastrar a la ranura y arrastrar regiones (diferido de T5)

**Qué falta.**

- **Arrastrar un archivo a una ranura** (voz, música o video), que D-4 pide junto a «Del historial» y «Archivo…». Hace falta mapear la posición del drop de Tauri (`getCurrentWebview().onDragDropEvent`) a la ranura bajo el cursor: el drop no dice a qué elemento cae. Sin AC que lo pruebe, queda fuera de T5.
- **Arrastrar regiones con el ratón** en la línea de tiempo. Hoy se mueven con flechas y se borran con Supr (AC-6 lo cubre así).

**Cómo seguir.** Un hook por ranura con una referencia al elemento; en el drop, comparar la posición (en px CSS, dividida por `devicePixelRatio`) con su `getBoundingClientRect()`. Probar con una posición simulada.

**Dónde.** `client/src/features/mix/MixSlot.tsx`, `MixTimeline.tsx`. Patrón existente: `client/src/features/narration/useScriptImport.ts`.
