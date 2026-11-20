# 010: la barra espaciadora lee la fase desde una referencia, no solo desde el estado

- **Contexto**: el atajo de Espacio se registra una vez en `window`. Con la fase solo en el estado, una pulsación justo después de empezar a grabar podía leer la fase anterior y volver a empezar la grabación.
- **Elegida**: `phaseRef` se actualiza junto con el estado, y el atajo llama a `toggleRef`, que se renueva en cada pintado. Espacio no hace nada mientras el micrófono abre (`starting`) o la toma sube (`uploading`). Espacio no se toma en campos ni en botones (`keepsSpace`).
- **Descartadas**: esperar a que React pinte antes de aceptar la tecla (no hay forma fiable de saberlo); deshabilitar el atajo mientras se abre el micrófono (el test de Espacio exige grabar, parar y subir con la tecla).
- **Cómo revertir**: quitar `phaseRef` y leer el estado `phase` en `toggle`.
- **Cómo comprobarla**: `RecordWizard.test.tsx`, «la barra espaciadora graba y, al pulsarla de nuevo, para y sube».
- **Pendiente**: ninguno.
