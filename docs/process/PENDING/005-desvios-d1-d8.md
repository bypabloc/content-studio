# 005: desvíos de D-1, D-2, D-4 y D-8 que quedan para después

- **Qué**: (1) cerrado en la 008: shadcn se copió a `shared/components/shadcn/` (ficha `WARNING/008-shadcn-codigo-de-proveedor.md`). (2) `Restablecer elecciones` confirma con `window.confirm`, no con `@tauri-apps/plugin-dialog` (D-8), que está en Cargo pero no en el paquete JS. (3) La CSP en `tauri.conf.json` es más amplia que la de D-2 (`img-src data: blob:`, `font-src data:`, `style-src 'unsafe-inline'`), necesaria para Tailwind y los iconos. (4) La fuente Geist no está instalada; se usa la del sistema. (5) El tema inicial se pinta con `public/theme-init.js`, un archivo externo, no con un script inline (la CSP lo exige).
- **Por qué no se hizo**: cada punto tiene un motivo técnico registrado y ninguno bloquea las pruebas de la 005.
- **Cuándo**: (2) y (4) antes del instalador (022); (1) y (3) cuando una sección los necesite.
- **Quién**: agente.
- **Qué la cierra**: la lista de arriba, cada punto resuelto o reconocido como decisión en su ficha WARNING.
