# 014: el servicio subtitles.create toma la GPU para todos sus orígenes

- **Contexto**: D-4 dice que `subtitles.create` usa el recurso `gpu` salvo el origen `import`. La cola toma el recurso por
  servicio, no por parámetro, y el limpiador (sin transcribir) también estaría detrás de la GPU.
- **Elegida**: `RESOURCE = 'gpu'` para el servicio entero. Así el candado se toma en la cola del mismo modo para todos los
  orígenes. Costo: un documento desde el limpiador o un SRT espera a que la GPU esté libre, aunque no la use.
- **Descartadas**: partir el servicio en dos (`subtitles.create` y `subtitles.import`), que duplica la validación y la
  API; o pasar el recurso como parámetro, que la cola no soporta hoy.
- **Cómo revertir**: cambiar `RESOURCE` en `services/subtitles_create.py` y separar el origen `import` en otro servicio.
- **Cómo comprobarla**: `validate` y `build_command` en `test_subtitles_create.py`; la espera de la GPU se ve en la cola.
