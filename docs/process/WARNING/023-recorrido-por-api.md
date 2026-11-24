# 023: el recorrido integral sobre la API del server instalado

- **Contexto**: la spec pide el recorrido encadenado en la app instalada. Manejar toda la UI por CDP habría pedido un escenario de `app-check` por sección (fuera del alcance de la 023), y Computer Use está prohibido en el repo.
- **Elegida**: instalar el NSIS fuera del repo (`content-studio-worktrees/023-it/`, carpeta de datos aislada con `CONTENT_STUDIO_HOME`), preparar la app con su primer arranque, instalar el paquete recomendado y correr cada paso contra `studio serve` del venv instalado (el mismo server que levanta Tauri), con los cuerpos que manda el client. La UI la cubren los e2e (84) y las capturas de `app-check` de la 022.
- **Descartadas**: un escenario de `app-check` por paso (mucho código de prueba nuevo); recorrer el checkout en modo desarrollo (no prueba la app instalada).
- **Cómo revertir**: no aplica (es la forma de verificar).
- **Cómo comprobarla**: el informe del PR de la 023, con las rutas y mediciones de cada paso.
- **Pendiente**: [023-recorrido-en-la-ui](../PENDING/023-recorrido-en-la-ui.md).
