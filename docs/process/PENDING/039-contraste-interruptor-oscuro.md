# 039: contraste del interruptor apagado y barra de desplazamiento en tema oscuro

- **Qué**: `image-reader` reporta, en las capturas del smoke (run `20261125-182130`): el interruptor «Identificar hablantes» apagado tiene poco contraste en claro y en oscuro (Transcripción, Subtítulos y Limpiador); la barra de desplazamiento de la barra lateral es blanca en oscuro; y el toast «Trabajo terminado» tapa parte del formulario (Transcripción, Hablantes, Subtítulos y Limpiador). Las lecturas son visuales, no medidas con un contraste numérico.
- **Por qué no se corrigió**: no bloquea la función, y falta medir el contraste antes de tocar el estilo.
- **Cuándo**: antes de publicar en `main`.
- **Quién**: el agente (medir y, si se confirma, ajustar el estilo del interruptor y de la barra en el client).
