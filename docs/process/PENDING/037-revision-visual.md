# 037: revisión visual de la sección Hablantes en oscuro

- **Qué**: en la captura de oscuro, el selector de «Hablantes» (Automático) tiene el texto gris sobre gris medio, con poco contraste; «Identificar», deshabilitado con el archivo vacío, se lee poco en claro y en oscuro; la barra de desplazamiento de la barra lateral se ve blanca en el tema oscuro.
- **Por qué no se hizo**: el selector y el botón son componentes compartidos con Transcripción (036) y el tema oscuro es global. Cambiarlos aquí alcanza a otras secciones; no bloquea la spec.
- **Cuándo**: después de publicar, junto con la revisión de contraste de 036 (`PENDING/036-corrida-real`, capturas con hablantes).
- **Quién**: agente.
- **Qué la cierra**: contraste del selector y del botón deshabilitado en oscuro y claro, medido con `image-reader` sobre `tmp/app-check/<run>/shots/speakers-check-*.png`, y la barra de desplazamiento del tema oscuro corregida en `client/src/shared/`.
