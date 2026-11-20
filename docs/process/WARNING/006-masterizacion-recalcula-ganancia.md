# 006: regenerar un párrafo recalcula la ganancia de toda la toma

- **Contexto**: la masterización (`master: voice`, a −16 LUFS) calcula la ganancia sobre la toma entera. Al regenerar un párrafo, la toma nueva la vuelve a calcular. Los bloques que no cambian quedan iguales en disco (AC-3: los bloques 0 y 2 de la prueba real son idénticos, `tmp/spec-006/ac3-blocks.txt`), pero en el `.wav` final el nivel de los párrafos que no se regeneraron no queda idéntico. Lo encontró la revisión `wf_bfce4603-274`.
- **Elegida**: no cambiar la masterización en 006. El `.wav` final cumple lo que pide la spec (−16 LUFS, sin recortes). Lo que AC-3 garantiza es el bloque, no el nivel exacto de cada párrafo en el `.wav` final.
- **Por qué no se corrige ahora**: fijar la ganancia por bloque cambiaría el sonido de todas las tomas, también de la original. Guardar la ganancia de la toma en `script.json` y reusarla al regenerar cambia el formato del guion: va más allá de la 006 (`plan-format.md` §0).
- **Descartadas**: normalizar cada bloque por separado (cambia el sonido de la toma original).
- **Cómo revertir**: no aplica; no hay código nuevo en esta decisión.
- **Cómo comprobarla**: `server/tests/unit/src/content_studio/services/test_narration_regenerate.py` (AC-3, bloques iguales) y, en el `.wav` final de las tomas 11 y 12 de la corrida 4 (`logs/spec-006-driver-corrida4.log`), comparar los párrafos 1 y 3.
- **Qué la cierra**: decisión del usuario sobre si ese cambio de nivel es aceptable. Si no lo es, guardar la ganancia de la toma en `script.json` y reusarla al regenerar, en una spec propia.
- **Antes de**: el pase a `main`. No bloquea el merge a `dev`.
