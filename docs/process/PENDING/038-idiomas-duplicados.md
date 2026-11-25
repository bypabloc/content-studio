# 038: la lista de idiomas está repetida en tres sitios

- **Qué**: `SubtitlesPage.tsx` y `TranscriptionForm.tsx` repiten los códigos `auto, es, en, pt, fr, de, it`, y el Limpiador usa la misma lista. Un idioma nuevo hay que añadirlo en los tres.
- **Cuándo**: después de publicar.
- **Quién**: agente.
- **Qué lo cierra**: una constante compartida o un selector de idioma en `shared/` que usen los tres.
