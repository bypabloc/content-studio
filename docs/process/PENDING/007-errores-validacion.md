# 007: los 422 de validación de FastAPI salen en inglés y fuera del catálogo

- **Qué**: los errores de validación de la ruta (un parámetro que no cumple su tipo, un cuerpo mal formado) los arma FastAPI con su formato `detail` y su texto en inglés. No pasan por `_http_error`, así que no tienen `code`, no usan `Accept-Language` y no están en `messages/`.
- **Por qué no se hizo**: fuera de alcance de la 007. Traducirlos exige un manejador de `RequestValidationError` que dé códigos y textos nuevos para cada caso, y eso es una decisión de contrato de la API (ver WARNING 007-job-id-entero).
- **Cuándo**: después de la 007, con la primera pantalla que muestre un 422 al usuario.
- **Quién**: agente.
- **Qué la cierra**: un manejador de `RequestValidationError` que responda `{code: 'validation', params, message}` con el texto de `error.validation` en el idioma pedido, y una prueba con un `job_id` no numérico.
