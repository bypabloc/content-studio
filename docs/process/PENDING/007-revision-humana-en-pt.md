# 007: una persona revisa `en.json` y `pt.json`, que los tradujo el agente

- **Qué**: las traducciones al inglés y al portugués (pt-BR) las escribió el agente al ejecutar la spec. Pueden tener frases poco naturales o términos que no coinciden con el resto de la app.
- **Por qué no se hizo**: no hay revisor humano disponible al ejecutar; la etapa `i18n` solo comprueba que las claves existan, tengan los mismos parámetros y no estén vacías.
- **Cuándo**: después de la 007, antes de la primera versión que se publique en `main`.
- **Quién**: el usuario, o quien revise el idioma.
- **Qué la cierra**: una persona lee `server/src/content_studio/messages/en.json` y `pt.json` y corrige las claves que marque; el cambio va en un commit aparte.
