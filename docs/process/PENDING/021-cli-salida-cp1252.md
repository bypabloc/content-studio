# 021: el JSON de `studio` sale en cp1252 cuando la salida va a un pipe en Windows

- **Qué**: `studio llm script-review … | otra-cosa` (y los demás comandos que imprimen JSON con `ensure_ascii=False`: `jobs list`, `engines list`, `library list`, `mix`, `editor`) escriben las tildes en cp1252 si stdout no es una consola. Quien lo lee como UTF-8 ve «gu�a». En la consola se ve bien, y `PYTHONIOENCODING=utf-8` lo evita.
- **Por qué no se hizo**: es de todo el CLI (spec 004), no del asistente; la verificación de la 021 usó `PYTHONIOENCODING=utf-8` y `result.json`.
- **Cuándo**: antes de publicar, o en la spec del instalador (022), que es cuando otros programas leerán la salida.
- **Quién**: agente.
- **Qué la cierra**: `sys.stdout.reconfigure(encoding='utf-8')` al entrar en `cli/main.py` (o `ensure_ascii=True`) y una prueba que lea la salida de un subproceso como UTF-8.
