# 031: el conversor no toma target del enlace

- **Qué**: `content-studio://new/media.convert?input=…&target=mp3` valida el parámetro y rellena el archivo, pero el formato no cambia: `FormatPicker` guarda su valor dentro y no acepta uno inicial.
- **Por qué queda así**: cambiar el selector excede el alcance de F1 (C3). El archivo sí se rellena (AC-3 del Conversor).
- **Cómo cerrarlo**: que `FormatPicker` reciba un `FormatChoice` inicial y `ConvertPage` le pase el de `target`; una prueba en `ConvertPage.test.tsx` con `setPrefill('convert', { path, target })`.
- **Cuándo**: antes de publicar 031 (verificación final).
