# 007: el catálogo de textos vive en el paquete del server y el client lo importa con `@messages`

- **Contexto**: el client necesita los textos al compilar y también antes de que arranque el server (su pantalla de arranque y el error de arranque se ven antes de que exista la API).
- **Elegida**: `server/src/content_studio/messages/{es,en,pt}.json` es la única fuente. El client lo importa con el alias `@messages` (`vite.config.ts`, `tsconfig`), con `server.fs.allow` para el modo dev de Vite. El server lo lee en tiempo de ejecución, y viaja con el paquete del server.
- **Descartadas**:
  - Una carpeta `messages/` en la raíz: no viaja en el paquete del server.
  - Servir el catálogo por `GET /messages/{lang}`: el client lo necesita antes de que arranque el server.
  - Dos catálogos con un script que los sincroniza: dos fuentes de lo mismo.
- **Cómo revertir**: mover la carpeta y cambiar el alias en `vite.config.ts` y `tsconfig`; no hay cambios de datos.
- **Cómo comprobarla**: `python -m devtools test-runner --type=i18n` pasa, y `bun run --cwd client build` compila con el alias.
- **Antes de**: el merge a `main`. La spec del instalador (022) debe comprobar que la carpeta `messages/` sale dentro del paquete instalado.
