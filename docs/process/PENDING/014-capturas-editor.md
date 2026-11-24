# 014: capturas del editor, origen desde archivo y cuadros de la quema

**Qué queda.** La batería de `03-verificacion-final.md` pide: capturas del editor en claro y en oscuro (punto 9); cuadros de la quema con `reels` y `classic` (punto 3), comparados con la vista previa JASSUB en el mismo tiempo por `image-reader`; y un proyecto creado desde un archivo real con `large-v3-turbo` (punto 2).

**Por qué no se hizo.** Requiere la app de escritorio con un video real cargado en el editor y `image-reader` para las imágenes. Lo que sí está verificado sin imágenes: la quema con libass (AC-6, ficha `014-quemar`), las fuentes (AC-8) y la UI del editor en e2e (44 pruebas en verde).

**Qué hacer.** Abrir un proyecto con video real, sacar las capturas en `tmp/spec-014/`, sacar los cuadros quemados a los mismos tiempos y pedir a `image-reader` la comparación (posición, fuente, color de resaltado y que el texto no caiga en la zona segura de Reels).
