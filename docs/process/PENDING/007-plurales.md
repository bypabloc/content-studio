# 007: los textos que dependen de un número no tienen plurales

- **Qué**: el catálogo no tiene formas de plural (`_one` y `_other`). Hoy ningún texto cambia según un número, así que la 007 no las agrega.
- **Por qué no se hizo**: ningún texto de la 007 depende de un número; agregar la infraestructura sería una abstracción sin uso (K.I.S.S., `plan-format.md` §0).
- **Cuándo**: en la primera spec que muestre un texto con un número (por ejemplo, «1 trabajo» / «3 trabajos»).
- **Quién**: agente.
- **Qué la cierra**: esa spec suma `_one` y `_other` en los tres catálogos y usa `Intl.PluralRules` en el client, con una prueba que compruebe ambas formas en `es`, `en` y `pt`.
