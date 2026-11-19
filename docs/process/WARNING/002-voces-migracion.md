# 002: migrar las voces construidas a inglés (archivos de estilo y aprobacion.json)

- **Qué**: `move-data --apply` (aplicado el 09:07 en el checkout principal) movió `voces/` a `voices/` y `voz/` a `reference/`, pero no renombró los archivos de estilo dentro de cada voz. Quedan `voices/<voz>/amistosa.wav`, `dramatica.wav`… y cada `aprobacion.json` con claves en español (`voz`, `aprobada`, `criterios`, `estilos`) y nombres de estilo en español. El código de la rama espera nombres en inglés, así que ninguna de las 15 voces construidas pasa `approved_voices` («rechazada en 10/12 estilos»).
- **Por qué no se hizo**: AC-4 pide renombrar esos `.wav` y `.txt` según la tabla de la spec, pero el reporte del apply no los incluye. Renombrar archivos de voces construidas y reescribir su `aprobacion.json` es categoría `user-data`: la spec no sobrescribe voces construidas sin el usuario.
- **Opciones**:
  - (a) **Migrar con respaldo (recomendado)**: copiar cada carpeta de voz a un respaldo, renombrar los `.wav` y `.txt` de estilo según la tabla y reescribir `aprobacion.json` a inglés (claves y estilos). Requiere confirmación del usuario.
  - (b) **Mantener en español**: el código lee un mapa de estilos español↔inglés. No toca datos; se aparta de AC-4 y deja deuda.
  - (c) **Pausar**: no fusionar; revisar el apply de `move-data` con calma.
- **Qué la cierra**: la opción elegida y `narration tts --voice <voz>` con una voz aprobada en los 12 estilos.
- **Quién decide**: el usuario.
- **Bloquea**: el merge a `dev`. Sin voces aprobadas, `narration tts --voice` no tiene voces que usar.
- **Resultado**: el usuario eligió la opción (a). Respaldo previo en `tmp/respaldo-voces-002/` (290 MB, copia idéntica verificada con `diff -rq`). Se renombraron 300 archivos de estilo (`.wav` y `.txt`) y se reescribieron las 15 aprobaciones con claves en inglés. Todo se verificó contra el respaldo: los bytes de cada archivo renombrado y los valores `ok`, `sim` y `approved`. Quedan aprobadas en los 12 estilos: andrea, colombia-m, hannah, karen-savage, mpinedag, peru-f, vctk-p345, venezuela-f y yesid. Las otras 6 siguen rechazadas en algún estilo: es el resultado real de la evaluación, no un problema de formato.
