# 017: la grabación admite compensación de latencia configurable

- **Contexto**: el micrófono y el dispositivo de salida pueden introducir latencia distinta en cada equipo; una compensación fija no sirve para todos.
- **Elegida**: guardar `editor.record_offset_ms` por usuario, con rango de -200 a 200 ms y valor inicial 0. El usuario lo ajusta con una palmada sobre la vista previa.
- **Descartadas**:
  - Aplicar un valor fijo del fabricante: no se puede inferir el búfer real del micrófono y de la salida.
  - Cambiar el valor durante el render: ocultaría el desfase y alteraría la línea de tiempo guardada.
- **Cómo revertir**: dejar el ajuste en 0 ms y retirar el control de compensación del Editor.
- **Cómo comprobarla**: pruebas de `useTrackRecorder.ts` validan el offset aplicado al comienzo de cada toma.
- **Pendiente**: medir con micrófono y auriculares físicos; el micrófono virtual de Playwright no valida la latencia acústica.
