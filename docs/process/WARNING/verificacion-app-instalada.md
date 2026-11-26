# Verificación sobre la app instalada (pasos que solo hace una persona)

- **Contexto**: todo se probó desde el checkout, con `app-check` (binario de desarrollo) y por la API. Lo que sigue necesita instalar encima de la instalación del usuario, aceptar un UAC, usar otro equipo o cerrar la sesión de Windows. Computer Use está prohibido y `app-check` no lo cubre.
- **Elegida**: un solo recorrido antes de `main`, con el instalador de la v0.1.0:
  1. **Instalar** encima de la instalación actual, con permiso del usuario porque cambia sus datos y su versión. El agente corre `python -m devtools app-check run --binary=<instalador> --scenario=installed --scenario=031-sendto`.
  2. **Actualizar** desde una versión anterior: el server viejo se detiene y arranca el nuevo (AC-9 de la 028).
  3. **Red local**: activarla, aceptar el UAC y ver la regla con `netsh advfirewall firewall show rule name="Content Studio LAN"` (solo perfil Privado). Desde un celular u otra PC: emparejar, subir, convertir y bajar (`docs/operations/lan.md`).
  4. **Inicio con Windows**: activar el interruptor, cerrar sesión, volver a entrar y comprobar que `uv run studio api status` dice `alive`.
  5. **Hablantes con un clip real de dos personas**: escuchar cada `speakers/*.wav` (solo su hablante). En la app, renombrar un hablante en Transcripción, ver los turnos en Hablantes y ver la vista previa y el quemado de Subtítulos con el color de cada hablante.
- **Descartadas**: instalar sin preguntar (pisaría la versión del usuario).
- **Cómo revertir**: no aplica.
- **Cómo comprobarla**: `report.json` de `app-check --binary` en verde y los pasos 2 a 5 anotados en esta ficha antes de borrarla.
