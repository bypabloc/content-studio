# 010: el texto del consentimiento se guarda en español, aunque la UI esté en otro idioma

- **Contexto**: `profile.json` guarda `consent: {accepted_at, text}` con el texto de `voice.consent.import`. `messages.t` usa `es` si no se le pasa idioma.
- **Elegida**: el texto en `es`, fijo. Es el registro de un permiso: no debe cambiar si el usuario cambia el idioma de la app después de aceptar.
- **Descartadas**: usar el idioma de `Accept-Language` (el registro cambiaría según la UI de cada momento); guardar las tres versiones (datos que nadie lee).
- **Cómo revertir**: pasar el idioma de la petición a `profiles.record_consent` (cambio de una línea en `voices_import.py`).
- **Cómo comprobarla**: `test_ac6_a_10_second_span_of_a_video_becomes_a_take_and_the_consent_is_recorded` comprueba que `consent.text` no queda vacío; el texto guardado es el de `messages/es.json`.
- **Pendiente**: ninguno.
