# 010: el progreso de un perfil cuenta los 12 estilos obligatorios del kit

- **Contexto**: D-6 pide «9 de 12 estilos» en la lista de perfiles. El kit tiene 13 estilos: los 12 obligatorios y el susurro, opcional. `GET /voices/profiles` devuelve solo los estilos con referencia y no dice cuántos son obligatorios.
- **Elegida**: la pantalla pide `GET /voices/kit` (una vez, sin caducidad) y cuenta solo los estilos no opcionales. Mientras el kit no llega, la tarjeta no muestra progreso, para que no aparezca un «0 de 0».
- **Descartadas**: fijar 12 en el client (se desincroniza si el kit cambia); agregar `done` y `total` a la respuesta del server (cambio de contrato en la parte del servidor ya cerrada en el 7a).
- **Cómo revertir**: la cuenta vive en `MyVoicesPage.tsx` (`required`), en un solo lugar.
- **Cómo comprobarla**: `client/tests/unit/src/features/voices/MyVoicesPage.test.tsx` (9 de 12, con `aria-valuenow` 0.75).
- **Pendiente**: ninguno.
