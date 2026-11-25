# 029: FileBrowser: un test de editor expiró una vez en el gate de 029

- **Qué**: `client/tests/unit/src/features/editor/browser/FileBrowser.test.tsx` > «restaura favoritas y muestra el error si
  falla el guardado» expiró (5 s) en una corrida completa de `test-runner --type=all`. Aislado pasa 10 de 10 dos veces, y
  la etapa `client-unit` completa pasó en el reintento.
- **Por qué no es de 029**: el test del editor no toca MCP. Es el mismo patrón de tiempo real que
  [028-suite-intermitente](028-suite-intermitente.md).
- **Quién decide**: agente.
- **Qué lo cierra**: que el test espere por condición con un plazo mayor, como con `028-suite-intermitente`. Revisar si
  vuelve a fallar en un gate.
