# 014: verificación del ASS con ffmpeg

- **Contexto**: AC-3 pide que el ASS lo acepte `ffmpeg -i x.ass -f null -`. Ese comando falla con «Output file does not
  contain any stream» (medido): `-f null` no mapea los streams de subtítulos por defecto, y `-map 0:s -f null` falla con
  «Default encoder for format null (codec none) is probably disabled».
- **Elegida**: la prueba `test_ac3_the_generated_ass_is_accepted_by_ffmpeg` corre `ffmpeg -v error -i x.ass -c:s ass -f ass -`
  y comprueba que la salida tiene todos los `Dialogue` (3 de 3). Con esto ffmpeg lee el archivo entero.
- **Límite medido**: ffmpeg es permisivo. Un `Dialogue` malformado (`Dialogue: 0,garbage`) pasa sin error y sale en la
  reescritura, así que el control de conteo no lo distingue. La validez de cada línea la cubren los tests de texto de
  `test_ass.py`. La validación con libass real llega con el quemado (T5).
- **Descartadas**: `-map 0:s -f null` (encoder null sin soporte de subtítulos); un parser ASS propio (más código sin
  AC que lo pida).
- **Cómo revertir**: no aplica (sin cambio de código por esta decisión).
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/subtitles/test_ass.py`.
