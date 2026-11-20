# 010: el e2e de Mis voces y de la grabación no existe todavía ni se ha corrido

- **Qué**: los e2e de Playwright de Mis voces y del asistente (abrir un perfil, Grabar, subir una toma con la API grabada) no están escritos ni corridos. `e2e` no está en `all`.
- **Por qué no se hizo**: el e2e se corre a mano al cerrar la spec, con el server real (regla de `e2e` fuera de `all`).
- **Cuándo**: al cerrar la 010 (T8 o T9).
- **Quién**: agente.
- **Qué la cierra**: `python -m devtools test-runner --type=e2e` en verde con los casos nuevos.
