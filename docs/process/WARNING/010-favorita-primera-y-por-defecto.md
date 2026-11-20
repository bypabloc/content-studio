# 010: el selector de voz pone la favorita primero y la usa por defecto

- **Contexto**: AC-9 pide que la voz favorita aparezca primero en el selector de voz de Narración. `UIRecommendedSelect` toma la primera opción como valor por defecto cuando ninguna está marcada como recomendada, y las voces no traen recomendada.
- **Elegida**: `VoiceSelect` pone primero las favoritas (`favoritesFirst`). Sin elección guardada, la voz por defecto es la primera opción: la favorita, si hay una.
- **Descartadas**: marcar una voz como recomendada. El catálogo no trae un criterio para elegirla.
- **Cómo revertir**: quitar `favoritesFirst` de la lista de opciones en `client/src/features/voices/VoiceSelect.tsx`. La prueba de orden dejaría de pasar y habría que decidirlo otra vez.
- **Cómo comprobarla**: `client/tests/unit/src/features/voices/VoiceSelect.test.tsx`.
