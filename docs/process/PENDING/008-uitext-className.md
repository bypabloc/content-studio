# 008: `UIText` concatena `className` sin fusionarlo

- **Qué**: `UIText` escribe `${base} ${className}`, mientras que `UIButton` y `UIIconButton` usan `cn`. Si `className` trae un color o una tipografía que la variante ya define, quedan los dos y gana el que aparece después en el CSS.
- **Por qué no se hizo**: en los organismos de T4 no hay un conflicto que se vea en los tests; el cambio tocaría un átomo ya comprometido en T2.
- **Cuándo**: T5, al revisar el shell y los textos del tema.
- **Quién**: agente.
- **Qué la cierra**: `UIText` usa `cn` y una prueba muestra que un `className` de color reemplaza el de la variante.
